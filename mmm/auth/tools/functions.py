# Copyright (c) 2024 Thomas Jurczyk
# This software is provided under the MIT License.
# For more information, please refer to the LICENSE file in the root directory of this project.

from flask import render_template, current_app
from flask_mail import Message
from mmm import mail
from itsdangerous.url_safe import URLSafeSerializer as Serializer

def confirm(token: str, text: str) -> bool:
    '''Confirm the email change or password reset request.
    
        Arguments
        ---------
        token: str
                The token to be confirmed.
        
        text: str
                The email address to be confirmed or the token generated to reset password.

        Returns
        -------
        bool
    '''
    s = Serializer(current_app.config['SECRET_KEY'])
    try:
        data = s.loads(token, max_age=3600)
    except:
        return False
    return data.get('confirm') == text

def generate_confirmation_token(text: str):
    '''Generate a token for email/password change confirmation.

       Arguments
       ---------
         text: str
              The email which change should be confirmed or the text to create a token for password reset.

            expiration: int
                The time in seconds the token should be valid.
        
        Returns
        -------
            str
                The token.
    '''
    s = Serializer(current_app.config['SECRET_KEY'])
    return s.dumps({'confirm': text})

def send_confirmation_email(to: str, subject: str, template: str, token: str, **kwargs):
    '''Send an email to confirm an email change.

       Arguments
       ---------
         to: str
              The email address to which the email should be sent.

         subject: str
              The subject of the email.

         template: str
              The template name to be used for the email.

         **kwargs
              The keyword arguments to be passed to the template.
    '''
    msg = Message(current_app.config['MMM_MAIL_SUBJECT_PREFIX'] + subject,
                  sender=current_app.config['MMM_MAIL_SENDER'], recipients=[to])
    msg.body = render_template(f"auth/email/{template}.txt", token=token, **kwargs)
    #msg.html = render_template(f"email/{template}.txt", **kwargs)
    mail.send(msg)