from flask import Flask
import os
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_admin import Admin
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail
from flask_migrate import Migrate

db = SQLAlchemy()
login_manager = LoginManager()
flask_admin = Admin()
csrf = CSRFProtect()
mail = Mail()
migrate = Migrate()

def create_app() -> Flask:
    '''Main function to create the Flask app. This function initializes the app, sets the configuration, and registers the blueprints, extensions, and login manager. It also sets up logging. This function is used in the main ws

    Returns
    -------
        Flask
            The Flask app.
    
    '''

    app = Flask(__name__, instance_relative_config=True)

    # Set config
    # Note: If you prefer to use environment variables for critical values, you can do so; environment variables will override the config file. 
    try:
        app.config.from_pyfile('../mmm.cfg')
    except FileNotFoundError:
        print('Config file not found. You need to provide a config file "mmm.cfg" in the root directory. Shutting down.')
        exit(1)
    
    # Check if environment variables are set
    # If so, override the config file
    if 'SECRET_KEY' in os.environ:
        app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
    if 'SQLALCHEMY_DATABASE_URI' in os.environ:
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['SQLALCHEMY_DATABASE_URI']
    if 'MAIL_SERVER' in os.environ:
        app.config['MAIL_SERVER'] = os.environ['MAIL_SERVER']
    if 'MAIL_PORT' in os.environ:
        app.config['MAIL_PORT'] = os.environ['MAIL_PORT']
    if 'MAIL_USE_TLS' in os.environ:
        app.config['MAIL_USE_TLS'] = os.environ['MAIL_USE_TLS']
    if 'MAIL_USERNAME' in os.environ:
        app.config['MAIL_USERNAME'] = os.environ['MAIL_USERNAME']
    if 'MAIL_PASSWORD' in os.environ:
        app.config['MAIL_PASSWORD'] = os.environ['MAIL_PASSWORD']
    if 'LOG_FILE' in os.environ:
        app.config['LOG_FILE'] = os.environ['LOG_FILE']
    if 'VERIFYBIBTEX_IMAGE' in os.environ:
        app.config['VERIFYBIBTEX_IMAGE'] = os.environ['VERIFYBIBTEX_IMAGE']
    if 'DOC2MD_IMAGE' in os.environ:
        app.config['DOC2MD_IMAGE'] = os.environ['DOC2MD_IMAGE']
    if 'XML2YAML_IMAGE' in os.environ:
        app.config['XML2YAML_IMAGE'] = os.environ['XML2YAML_IMAGE']
    if 'TYPESETTING_IMAGE' in os.environ:
        app.config['TYPESETTING_IMAGE'] = os.environ['TYPESETTING_IMAGE']

    # Register csrf
    csrf.init_app(app)

    # Register mail
    mail.init_app(app)

    # Register database
    db.init_app(app)
    
    # Register migrate
    migrate.init_app(app, db)

    # Add logging
    import logging
    from logging import FileHandler, Formatter
    file_handler = FileHandler(app.config['LOG_FILE'])
    app.logger.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    file_handler.setFormatter(Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d]'
    ))
    
    from mmm.routes import main
    app.register_blueprint(main)

    from mmm.auth import auth
    app.register_blueprint(auth)

    from mmm.maker import maker
    app.register_blueprint(maker)
    
    from mmm.maker_project import maker_project
    app.register_blueprint(maker_project)

    # Register login manager
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    from mmm.auth.models import User, UserAdminView
    # Register flask admin
    flask_admin.init_app(app) 

    flask_admin.add_view(UserAdminView(User, db.session))

    return app