# Copyright (c) 2024 Thomas Jurczyk
# This software is provided under the MIT License.
# For more information, please refer to the LICENSE file in the root directory of this project.

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField, SubmitField
from wtforms.validators import InputRequired

class LoginForm(FlaskForm):
    username = StringField('Username', [InputRequired()])
    password = PasswordField('Password', [InputRequired()])

class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Old Password', [InputRequired()])
    new_password = PasswordField('Password', [InputRequired()])
    password_confirm = PasswordField('Confirm Password', [InputRequired()])
    submit = SubmitField('Change Password')

class ChangeEmailForm(FlaskForm):
    email = EmailField('Email', [InputRequired()])
    submit = SubmitField('Change Email')

class ResetPasswordRequestForm(FlaskForm):
    email = EmailField('Email', [InputRequired()])
    submit = SubmitField('Reset Password')

class ResetPasswordForm(FlaskForm):
    new_password = PasswordField('Password', [InputRequired()])
    password_confirm = PasswordField('Confirm Password', [InputRequired()])
    submit = SubmitField('Reset Password')