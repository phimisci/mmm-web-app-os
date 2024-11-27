from mmm import db
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import PasswordField
from flask_login import UserMixin, current_user
from flask_admin.contrib.sqla import ModelView

## USER MODEL
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    email = db.Column(db.String(100), unique=True)
    # Field to temporarily store a new not yet confirmed email address
    email_change = db.Column(db.String(100))
    # Salt stored for password reset
    salt = db.Column(db.String(16))
    pwdhash = db.Column(db.String())
    admin = db.Column(db.Boolean())
    
    def __init__(self, username, password, email, admin=False):
        self.username = username
        self.pwdhash = generate_password_hash(password)
        self.email = email
        self.admin = admin
    
    def check_password(self, password):
        return check_password_hash(self.pwdhash, password)
    
    def is_admin(self):
        return self.admin
    
## USER ADMIN FORMS
class UserAdminView(ModelView):
    column_searchable_list = ('username', 'email')
    column_sortable_list = ('username', 'admin', 'email')
    column_exclude_list = ('pwdhash', 'email_change', 'salt')
    form_excluded_columns = ('pwdhash', 'email_change', 'salt')
    form_edit_rules = ('username', 'admin', 'email')
    
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin()
    
    def scaffold_form(self):
        form_class = super(UserAdminView, self).scaffold_form()
        form_class.password = PasswordField('Password')
        return form_class
    
    def create_model(self, form):
        model = self.model(form.username.data, form.password.data, form.email.data, form.admin.data)
        form.populate_obj(model)
        self.session.add(model)
        self._on_model_change(form, model, True)
        self.session.commit()