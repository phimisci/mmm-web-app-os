from . import auth
from mmm import db, login_manager
from flask import request, render_template, redirect, url_for, flash, current_app
from .models import User
from .forms import LoginForm, ChangeEmailForm, ChangePasswordForm, ResetPasswordRequestForm, ResetPasswordForm
from flask_login import current_user, login_user, logout_user, login_required
import datetime
from .tools import send_confirmation_email, generate_confirmation_token, confirm
from werkzeug.security import generate_password_hash
import os

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

## LOGOUT ROUTE
@auth.route('/logout')
@login_required
def logout():
    # logging
    username: str = current_user.username if current_user.is_authenticated else "Anonymous"
    current_app.logger.info(f"User {username} logged out.")
    logout_user()
    flash('You have successfully logged out.', 'success')
    return redirect(url_for('main.index'))

## LOGIN ROUTE
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        flash('You are already logged in.', 'info')
        return redirect(url_for('main.select_maker'))
    form = LoginForm()
    if form.validate_on_submit():
        username = request.form.get('username')
        password = request.form.get('password')
        existing_user = User.query.filter_by(username=username).first()
        if not (existing_user and existing_user.check_password(password)):
            flash('Invalid username or password. Please try again.', 'danger')
            return render_template('auth/login.html', form=form)
        login_user(existing_user, remember=True, duration=datetime.timedelta(minutes=30))
        flash('You have successfully logged in.', 'success')
        # logging
        username: str = current_user.username if current_user.is_authenticated else "Anonymous"
        current_app.logger.info(f"User {username} now logged in.")
        return redirect(url_for('main.select_maker'))
    if form.errors:
        flash(form.errors, 'danger')
    return render_template('auth/login.html', form=form)

## USER SETTINGS ROUTE
@auth.route('/user_settings')
@login_required
def user_settings():
    change_password_form = ChangePasswordForm()
    email_form = ChangeEmailForm()  
    return render_template('auth/user-settings.html', email_form=email_form, change_password_form=change_password_form)
    
## CHANGE EMAIL ROUTE
@auth.route('/change_email', methods=['POST'])
@login_required
def change_email():
    form = ChangeEmailForm()
    if form.validate_on_submit():
        email = form.email.data
        # Check if the email address is already in use
        if email == current_user.email:
            flash('This is already your email address.', 'info')
            return redirect(url_for('auth.user_settings'))
        # Check if the email address is already in use
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('This email address is already in use.', 'danger')
            current_app.logger.error(f"User {current_user.username} trying to change email address, but email address is already in use.")
            return redirect(url_for('auth.user_settings'))
        # Save the new email address in the user model; still needs to be confirmed
        current_user.email_change = email
        db.session.commit()
        # Create a token for email confirmation
        token = generate_confirmation_token(email)
        # Send an email to the new email address
        send_confirmation_email(email, "Email Address Change Confirmation", "email_change", new_email=email, token=token)
        flash("An email has been sent to your new email address. Please follow the instructions to complete the change.", "info")
        current_app.logger.info(f"User {current_user.username} is trying to change email address.")
        return redirect(url_for('auth.user_settings'))
    else:
        flash(form.errors, 'danger')
        current_app.logger.error(f"User {current_user.username} trying to change email address, but form validation failed: {form.errors}")
        return redirect(url_for('auth.user_settings'))

## CONFIRM EMAIL CHANGE ROUTE
@auth.route('/confirm_email/<token>')
@login_required
def confirm_email(token):
    # Get the email address to be confirmed
    email = current_user.email_change
    if confirm(token, email):
        current_user.email = email
        current_user.email_change = None
        db.session.commit()
        flash('Your email has been successfully changed.', 'success')
        current_app.logger.info(f"User {current_user.username} has successfully changed email address.")
        return redirect(url_for('auth.user_settings'))
    flash('The confirmation link is invalid or has expired.', 'danger')
    return redirect(url_for('main.index'))

## CHANGE PASSWORD ROUTE
@auth.route('/change_password', methods=['POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        old_password = form.old_password.data
        new_password = form.new_password.data
        confirm_password = form.password_confirm.data
        if not current_user.check_password(old_password):
            flash('The old password is incorrect.', 'danger')
            current_app.logger.info(f"User {current_user.username} trying to set new password, but the old password is incorrect.")
            return redirect(url_for('auth.user_settings'))
        if old_password == new_password:
            flash('The new password must be different from the old one.', 'danger')
            current_app.logger.info(f"User {current_user.username} trying to set new password, but new_password is the same as old one.")
            return redirect(url_for('auth.user_settings'))
        if new_password != confirm_password:
            flash('The new passwords do not match.', 'danger')
            current_app.logger.info(f"User {current_user.username} trying to set new password, but new_password and confirm_password don't match.")
            return redirect(url_for('auth.user_settings'))
        current_user.pwdhash = generate_password_hash(new_password)
        current_app.logger.info(f"User {current_user.username} has successfully changed password.")
        db.session.commit()
        flash('Your password has been successfully changed.', 'success')
        return redirect(url_for('auth.user_settings'))
    flash(form.errors, 'danger')
    current_app.logger.error(f"User {current_user.username} trying to set new password, but form validation failed: {form.errors}")
    return redirect(url_for('auth.user_settings'))

## RESET PASSWORD ROUTES

@auth.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        email = form.email.data
        user = User.query.filter_by(email=email).first()
        if user:
            # Generate a token + salt for password reset
            # Generate salt
            salt = os.urandom(16).hex()
            user.salt = salt
            db.session.commit()
            # Create a token for password reset
            token = generate_confirmation_token(email+salt)
            send_confirmation_email(email, "Password Reset Request", "reset_password_request", token=token, email=email)
            flash('An email has been sent to you with instructions on how to reset your password.', 'info')
            current_app.logger.info(f"User with email {email} requested password reset.")
            return redirect(url_for('main.index'))
        flash('No user with this email address was found.', 'danger')
        current_app.logger.info(f"User with email {email} requested password reset, but no user found.")
        return redirect(url_for('auth.reset_password_request'))
    return render_template('auth/reset-password-request.html', password_reset_request_form=form)

@auth.route('/reset_password/<email>/<token>', methods=['GET', 'POST'])
def reset_password(email, token):
    form = ResetPasswordForm()
    if form.validate_on_submit():
        password = form.new_password.data
        confirm_password = form.password_confirm.data
        if password != confirm_password:
            flash('The passwords do not match.', 'danger')
            return redirect(url_for('auth.reset_password', email=email, token=token))
        user = User.query.filter_by(email=email).first()
        if user:
            user.pwdhash = generate_password_hash(password)
            # Reset salt
            user.salt = None
            db.session.commit()
            flash('Your password has been successfully reset.', 'success')
            current_app.logger.info(f"User with email {email} has successfully reset password.")
            return redirect(url_for('auth.login'))
        flash('No user with this email address was found.', 'danger')
        current_app.logger.info(f"User with email {email} tried to reset password, but no user found.")
        return redirect(url_for('auth.reset_password_request'))
    else:
        user = User.query.filter_by(email=email).first()
        if user:
            # Get salt
            salt = user.salt
            if not salt:
                flash('No password request found or token already used.', 'danger')
                return redirect(url_for('main.index'))
            if confirm(token, email+salt):
                return render_template('auth/reset-password.html', email=email, token=token, reset_password_form=form)
    flash('The confirmation link is invalid or has expired.', 'danger')
    return redirect(url_for('main.index'))