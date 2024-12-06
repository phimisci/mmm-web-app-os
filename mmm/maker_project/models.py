# Copyright (c) 2024 Thomas Jurczyk
# This software is provided under the MIT License.
# For more information, please refer to the LICENSE file in the root directory of this project.

from mmm import db

class File(db.Model):
    __tablename__ = "files"
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    changed_at = db.Column(db.DateTime, nullable=False)
    production_file = db.Column(db.Boolean, nullable=False)
    download_number = db.Column(db.Integer, nullable=False)
    
    def __init__(self, filename, project_id, created_by, created_at, changed_at, production_file, download_number):
        self.filename = filename
        self.project_id = project_id
        self.created_by = created_by
        self.created_at = created_at
        self.changed_at = changed_at
        self.production_file = production_file
        self.download_number = download_number

    def __repr__(self):
        return f"File('{self.filename}', '{self.project_id}', '{self.created_at}', '{self.changed_at}', '{self.download_number}')"

class Project(db.Model):
    __tablename__ = "projects"
    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(255), nullable=False)
    project_name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    changed_at = db.Column(db.DateTime, nullable=False)
    
    def __init__(self, path, project_name, created_at, changed_at):
        self.path = path
        self.project_name = project_name
        self.created_at = created_at
        self.changed_at = changed_at

    def __repr__(self):
        return f"Project('{self.path}', '{self.project_name}', '{self.created_at}', '{self.changed_at}')"

class UserProject(db.Model):
    __tablename__ = "user_projects"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    permission = db.Column(db.String(255), nullable=False)
    creator = db.Column(db.Boolean, nullable=False)
    
    def __init__(self, user_id, project_id, permission, creator):
        self.user_id = user_id
        self.project_id = project_id
        self.permission = permission
        self.creator = creator

    def __repr__(self):
        return f"UserProject('{self.user_id}', '{self.project_id}', '{self.permission}', '{self.creator}')"