# Copyright (c) 2024 Thomas Jurczyk
# This software is provided under the MIT License.
# For more information, please refer to the LICENSE file in the root directory of this project.

from mmm import db, create_app
import os
from flask_migrate import upgrade
from flask import current_app

def create_admin() -> None:
    """
    Creates an admin user in the database if it doesn't already exist.

    This function checks if an admin user already exists in the database. If not, it creates a new admin user
    with the provided admin username, password, and email address. The admin user is then added to the database
    and committed.

    Returns
    -------
        None
    """
    print("Creating admin user...")
    # Check if admin user already exists
    admin_username, admin_password = search_admin_env()
    from mmm.auth.models import User
    if User.query.filter_by(username=admin_username).first() is not None:
        print("Admin user already exists.")
        return
    admin = User(admin_username, admin_password,  'admin@phimisci.org', True)
    db.session.add(admin)
    db.session.commit()
    print("Admin user created successfully.")

def search_admin_env() -> tuple:
    """
    Searches for the environment variables FLASK_ADMIN_USERNAME and FLASK_ADMIN_PASSWORD in the app.config.
    If found, returns their values. Otherwise, returns the default values ("admin", "admin").

    Returns
    -------
        tuple
            A tuple containing the admin username and password.
    """
    if current_app.config.get('FLASK_ADMIN_USERNAME') and current_app.config.get('FLASK_ADMIN_PASSWORD'):
        return current_app.config.get('FLASK_ADMIN_USERNAME'), current_app.config.get('FLASK_ADMIN_PASSWORD')
    else:
        return ("admin", "admin")

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        # Update database
        upgrade()
        create_admin()