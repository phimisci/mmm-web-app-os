from flask import request, render_template, redirect, flash, url_for, current_app, send_from_directory
from . import maker_project
from .tools import create_user_folder, create_new_project_func, get_all_projects_for_user, delete_project_from_db, allowed_file, file_exists, create_files, get_xml2yaml_data, create_html_verifybibtex, create_share_project_choices, send_email, critical_error_logger
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from mmm.auth.models import User
from mmm.maker_project.models import Project, File, UserProject
import shutil
from mmm import db
import os, re, stat
import tempfile
from mmm.maker_project.forms import UploadForm, CreateProjectForm, MMMDynamicForm, RenameObject, ShareProjectWithUser
from datetime import datetime
from typing import Literal
from flask_wtf.csrf import validate_csrf

### INDEX ROUTE

@maker_project.route('/')
@login_required
def index():
    # Currently redirects to show_user_projects route
    return redirect(url_for("maker_project.show_user_projects"))

#### PROJECT ROUTES

### Create project route

@maker_project.route('/create-new-project', methods=['GET', 'POST'])
@login_required
def create_new_project():
    form = CreateProjectForm()
    if form.validate_on_submit():
        # Get username of current user
        username = current_user.username
        # Make sure user folder exists in uploads/
        create_user_folder(username)
        # Create new project folder
        project_name = form.project_name.data
        res = create_new_project_func(project_name, username)
        # If creation failed, redirect to create_new_project route
        if res == 1:
            flash('Project already exists. Please choose a different project name.', 'info')
            critical_error_logger(f'Project {project_name} already exists for {username}.')
            return render_template("maker_project/create-new-project.html", form=form)
        # If project creation was successful, redirect to index route
        else:
            flash(f'Project {project_name} created successfully.', 'success')
            current_app.logger.info(f"Project folder {project_name} created for {username}.")
            return redirect(url_for("maker_project.index"))
    else:
        return render_template("maker_project/create-new-project.html", form=form)

### Delete project route

@maker_project.route('/delete-project/<int:project_id>', methods=['GET'])
@login_required
def delete_project(project_id):
    if request.method == 'GET':
        # Check user permission to delete project. Only creator can delete project.
        permission = UserProject.query.filter_by(user_id=current_user.id, project_id=project_id).first().creator
        username = current_user.username
        project_name = Project.query.get(project_id).project_name
        if permission:
            # Delete project from db
            delete_project_from_db(project_id)
            # Delete project folder
            project_folder = f"uploads/{username}/{project_name}"
            try:
                shutil.rmtree(project_folder)
                flash(f'Project {project_name} deleted successfully.', 'success')
                current_app.logger.info(f"Project folder {project_name} deleted for {username}.")
                return redirect(url_for("maker_project.show_user_projects"))
            except OSError as e:
                flash(f'An error occurred while deleting project {project_name}.', 'danger')
                critical_error_logger(f"Error deleting project folder {project_name} for {username}.")
                return redirect(url_for("maker_project.show_user_projects"))
        else:
            flash('Only the creator has permission to delete this project.', 'danger')
            critical_error_logger(f"Deleting folder {project_name} was not allowed for {username}.")
            return redirect(url_for("maker_project.show_user_projects"))

### Download project route

@maker_project.route('/download-folder/<int:project_id>/<string:download_instruction>/', methods=['GET'])
@login_required
def download_folder(project_id, download_instruction: Literal["all", "user", "production"]):
    '''This route is used to download a folder or certain files (user/production) from a project folder.

        Arguments
        ---------
        project_id : int
            The ID of the project to download.
        download_instruction : Literal["all", "user", "production"]
            The instruction to download all files or either the user or production folder.
    
    '''
    user_project = UserProject.query.filter_by(user_id=current_user.id, project_id=project_id).first()
    if not user_project:
        flash('Project not found or access denied.', 'danger')
        return redirect(url_for("maker_project.show_user_projects"))
    
    permission = user_project.permission
    if "r" in permission:
        project = Project.query.get(project_id)
        if project is None:
            flash('Project not found.', 'danger')
            return redirect(url_for("maker_project.show_user_projects"))

        project_name = project.project_name
        username = current_user.username
        project_path = project.path
        project_folder = os.path.join(os.getcwd(), project_path, project_name)
        # Using a temporary file to avoid conflicts and ensure cleanup
        if download_instruction == "all":
            with tempfile.TemporaryDirectory() as tmpdirname:
                zip_path = os.path.join(tmpdirname, f"{project_name}.zip")
                shutil.make_archive(zip_path.replace('.zip', ''), 'zip', project_folder)
                current_app.logger.info(f"Project folder {project_name} downloaded by {username}.")
                return send_from_directory(tmpdirname, f"{project_name}.zip", as_attachment=True)
        elif download_instruction == "user" or download_instruction == "production":
            with tempfile.TemporaryDirectory() as tmpdirname:
                # Get all user or production files
                is_production = True if download_instruction == "production" else False
                user_files = File.query.filter_by(project_id=project_id, production_file=is_production).all()
                # Copy all user/production files in a temporary folder
                for file in user_files:
                    file_path = os.path.join(project_folder, file.filename)
                    shutil.copy(file_path, tmpdirname)
                # Create zip file in yet another temporary folder
                with tempfile.TemporaryDirectory() as tmpdirname_zip:
                    zip_path = os.path.join(tmpdirname_zip, f"{project_name}_{download_instruction}_files.zip")
                    shutil.make_archive(zip_path.replace('.zip', ''), 'zip', tmpdirname)
                    current_app.logger.info(f"{download_instruction} files of folder {project_name} downloaded by {username}.")
                    return send_from_directory(tmpdirname_zip, f"{project_name}_{download_instruction}_files.zip", as_attachment=True)
    else:
        flash('You do not have permission to download this project.', 'danger')
        return redirect(url_for("maker_project.show_user_projects"))

### Rename project route

@maker_project.route('/rename-project/<int:project_id>', methods=['GET', 'POST'])
@login_required
def rename_project(project_id):
    form = RenameObject()
    project = Project.query.get(project_id)
    if form.validate_on_submit():
        # Get new name
        new_name = form.new_name.data
        # Replace spaces with underscores
        new_name = re.sub(r"\s+", "_", new_name)
        # Check if this project name already exists for this user
        if Project.query.filter_by(project_name=new_name, path=project.path).first():
            flash(f'Project {new_name} already exists. Please choose a different project name.', 'info')
            critical_error_logger(f'Project {new_name} already exists.')
            return render_template("maker_project/rename-project.html", form=form, project_id=project_id, project_name=project.project_name)
        # Get project details
        old_name = project.project_name
        # Check user permissions
        permission = UserProject.query.filter_by(user_id=current_user.id, project_id=project_id).first().permission
        # Get project details
        if "d" in permission:
            # Rename project folder
            username = current_user.username
            old_path = os.path.join(os.getcwd(), "uploads", username, old_name)
            new_path = os.path.join(os.getcwd(), "uploads", username, new_name)
            try:
                os.rename(old_path, new_path)
                # Set permissions to new folder; otherwise, download will not work (10.05.2024)
                permissions = stat.S_IWUSR | stat.S_IRUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IROTH
                os.chmod(new_path, permissions)
                # Update project name in db
                project.project_name = new_name
                db.session.commit()
                flash(f'Project {old_name} renamed to {new_name} successfully.', 'success')
                current_app.logger.info(f"Project folder {old_name} renamed to {new_name} by {username}.")
                return redirect(url_for("maker_project.show_user_projects"))
            except OSError as e:
                flash(f'An error occurred while renaming project {old_name}.', 'danger')
                critical_error_logger(f"Error renaming project folder {old_name} for {username}.")
                return redirect(url_for("maker_project.show_user_projects"))
        else:
            flash('You do not have permission to rename this project.', 'danger')
            critical_error_logger(f"Renaming folder {old_name} was not allowed for {username}.")
            return redirect(url_for("maker_project.show_user_projects"))
    else:
        project_name = project.project_name
        # Check user permissions
        permission = UserProject.query.filter_by(user_id=current_user.id, project_id=project_id).first().permission
        if "d" in permission:
            return render_template("maker_project/rename-project.html", form=form, project_id=project_id, project_name=project_name )
        else:
            flash('You do not have permission to rename this project.', 'danger')
            critical_error_logger(f"Renaming folder {project_name} was not allowed for {username}.")
            return redirect(url_for("maker_project.show_user_projects"))
        
### Share project route

@maker_project.route('/share-project/<int:project_id>', methods=['GET', 'POST'])
@login_required
def share_project(project_id):
    form = ShareProjectWithUser()
    # Populate user choices with all existing users in DB
    form.user.choices = [(-1, 'Select a user')] + [create_share_project_choices(user.id, project_id, user.username) for user in User.query.all() if user.id != current_user.id]
    # Get project details
    project = Project.query.get(project_id)
    if form.validate_on_submit():
        # Check if current user is creator of this project
        creator = UserProject.query.filter_by(user_id=current_user.id, project_id=project_id).first().creator
        if not creator:
            flash('You are not the owner of this project. You do not have permission to share this project with other users.', 'danger')
            critical_error_logger(f"Sharing project {project.project_name} was not allowed for {current_user.username}.")
            return redirect(url_for("maker_project.show_user_projects"))
        # Get user id
        user_id = form.user.data
        # Get user via id
        user = User.query.get(user_id)
        # Check if user exists
        if user is None:
            flash(f'User not found.', 'danger')
            critical_error_logger(f'User with ID {user_id} not found.')
            return redirect(url_for("maker_project.share_project", project_id=project_id))
        elif user.id == current_user.id: # Check if user is trying to share project with himself
            flash('You cannot share a project with yourself.', 'danger')
            critical_error_logger(f'User with ID {user_id} tried to share project with himself.')
            return redirect(url_for("maker_project.share_project", project_id=project_id))
        user_tag = user.username
        # Check if user permissions should be revoked
        user_project = UserProject.query.filter_by(user_id=user_id, project_id=project_id).first()
        if user_project:
            # Check if user wants to revoke access
            if form.revoke_permission.data:
                db.session.delete(user_project)
                db.session.commit()
                flash(f'Access to project {project.project_name} revoked for user {user_tag}.', 'success')
                current_app.logger.info(f'Access to project {project.project_name} revoked for user {user_tag}.')
                return redirect(url_for("maker_project.show_user_projects"))
        # Get permissions
        write_permission = "w" if form.write_permission.data else ""
        delete_permission = "d" if form.delete_permission.data else ""
        permission = "r" + write_permission + delete_permission
        # Share project with user
        # Get project (needed for email)
        project = Project.query.get(project_id)
        # If UserProject already exists, just update permissions
        if user_project:
            user_project.permission = permission
            db.session.commit()
            flash(f'Project {project.project_name} shared with user {user_tag} with {permission} rights.', 'success')
            current_app.logger.info(f'Project {project.project_name} shared with user {user_tag} with {permission} rights.')
            # Send email to user
            send_email(user.email, 'Project shared with you', 'project_shared_email', shared_user=user, project=project, permissions=permission)
            return redirect(url_for("maker_project.share_project", project_id=project_id))
        else:
            user_project = UserProject(user_id, project_id, permission, False)
            db.session.add(user_project)
            db.session.commit()
            flash(f'Project {project.project_name} shared with user {user_tag} with {permission} rights.', 'success')
            current_app.logger.info(f'Project {project.project_name} shared with user {user_tag} with {permission} rights.')
            # Send email to user
            send_email(user.email, 'Project shared with you', 'project_shared_email', shared_user=user, project=project, permissions=permission)
            return redirect(url_for("maker_project.share_project", project_id=project_id))
    else:
        return render_template("maker_project/share-project.html", form=form, project=project)

### Show single project files route

@maker_project.route('/show-project-files/<int:project_id>', methods=['GET', 'POST'])
@login_required
def show_project_files(project_id):
    form = UploadForm()
    error_msg = ""
    # Create list of users with access to this project
    user_list = UserProject.query.filter_by(project_id=project_id).all()
    # Get user names
    user_names = [User.query.get(user.user_id).username for user in user_list]
    if form.validate_on_submit():
        # Check if user has permission to upload files
        permission = UserProject.query.filter_by(user_id=current_user.id, project_id=project_id).first().permission
        if "w" not in permission:
            flash('You do not have permission to upload files.', 'danger')
            critical_error_logger(f"Uploading files was not allowed for {current_user.username}.")
            return redirect(url_for('maker_project.show_project_files', project_id=project_id))
        # Save files in project folder
        for f in form.files.data:
            if f and allowed_file(f.filename):
                filename = secure_filename(f.filename)
                # Check if file exists and rename old file
                file_exists(filename, project_id)
                # Get project data for file upload
                project = Project.query.get(project_id)
                project_name = project.project_name
                project_path = project.path
                f.save(os.path.join(project_path, project_name, filename))
                # Register file in database
                file_4db = File(filename, project_id, current_user.id, datetime.now(), datetime.now(), False, 0)
                db.session.add(file_4db)
                db.session.commit()
            else:
                error_msg += f"File type not allowed {f.filename}."
        if error_msg:
            flash(error_msg, 'danger')
        else:
            flash('File(s) have successfully been uploaded!', 'success')
        return redirect(url_for('maker_project.show_project_files', project_id=project_id))
    else:
        # Get project details
        project = Project.query.get(project_id)
        # Get all files for project
        files = File.query.filter_by(project_id=project_id).all()
        # Get permissions for current user
        permission = UserProject.query.filter_by(user_id=current_user.id, project_id=project_id).first().permission
        return render_template("maker_project/show-project-files.html", project=project, files=files, form=form, user_names=user_names, permission=permission)

### Show all projects route
    
@maker_project.route('/show-user-projects', methods=['GET', 'POST'])
@login_required
def show_user_projects():
    if request.method == 'GET':
        # Get all projects for current user
        owned_projects_list, shared_projects_list = get_all_projects_for_user(current_user.id)
        return render_template("maker_project/show-projects.html", owned_projects=owned_projects_list, shared_projects=shared_projects_list)

#### FILES ROUTES

### Delete single file route

@maker_project.route('/delete-file/<int:file_id>', methods=['GET'])
@login_required
def delete_file(file_id):
    if request.method == 'GET':
        # Get file and folder info
        file = File.query.get(file_id)
        filename = file.filename
        project_name = Project.query.get(file.project_id).project_name
        project_id = Project.query.get(file.project_id).id
        project_path = Project.query.get(file.project_id).path
        # Check user permissions
        permission = UserProject.query.filter_by(user_id=current_user.id, project_id=file.project_id).first().permission
        # Get file path
        file_in_dir = f"{project_path}/{project_name}/{filename}"
        # Get username 
        username = current_user.username
        # Delete file if d permission or if this user has created the file
        if "d" in permission or file.created_by == current_user.id: 
            # Delete file from db
            db.session.delete(file)
            db.session.commit()
            # Delete file in directory
            try:
                os.remove(file_in_dir)
                flash(f'File {filename} deleted successfully.', 'success')
                current_app.logger.info(f"File {file_in_dir} deleted by {username}.")
                return redirect(url_for("maker_project.show_project_files", project_id=project_id))
            except OSError as e:
                flash(f'An error occurred while deleting file {filename}.', 'danger')
                critical_error_logger(f"Error deleting file {filename} by {username}.")
                return redirect(url_for("maker_project.show_project_files", project_id=project_id))
        else:
            flash('You do not have permission to delete this file.', 'danger')
            critical_error_logger(f"Deleting file {file_in_dir} was not allowed for {username}.")
            return redirect(url_for("maker_project.show_project_files", project_id=project_id))

### Delete multiple files route

@maker_project.route('/delete-multiple-files', methods=['POST'])
@login_required
def delete_multiple_files():
    # Manually validate CSRF token since we are using a custom form for file selection
    csrf_token = request.form.get('csrf_token')
    validate_csrf(csrf_token)
    # Get list of file IDs
    file_ids = request.form.getlist('file-selection')
    if file_ids == []:
        flash('No files selected.', 'danger')
        return redirect(url_for("maker_project.show_user_projects"))
    project_id = File.query.get(file_ids[0]).project_id
    # Check user permissions
    permission = UserProject.query.filter_by(user_id=current_user.id, project_id=project_id).first().permission
    # Get project details
    project_name = Project.query.get(project_id).project_name
    project_path = Project.query.get(project_id).path
    username = current_user.username
    if "d" in permission:
        # Collect info for single flash message
        flash_success_msg = f'Files deleted successfully: '
        flash_error_msg = f'An error occurred while deleting files: '
        # Delete files from db
        for file_id in file_ids:
            file = File.query.get(file_id)
            filename = file.filename
            # Get file path
            file_in_dir = f"{project_path}/{project_name}/{filename}"
            # Delete file from db
            db.session.delete(file)
            db.session.commit()
            # Delete file in project folder
            try:
                os.remove(file_in_dir)
                flash_success_msg += f'{filename}, '
                current_app.logger.info(f"File {file_in_dir} deleted by {username}.")
            except OSError as e:
                flash_error_msg += f'{filename}, '
                critical_error_logger(f"Error deleting file {filename} by {username}.")
        # Create flash messages
        if flash_success_msg != 'Files deleted successfully: ':
            flash(flash_success_msg[:-2], 'success')
        if flash_error_msg != 'An error occurred while deleting files: ':
            flash(flash_error_msg[:-2], 'danger')
        return redirect(url_for("maker_project.show_project_files", project_id=project_id))
    else:
        flash('You do not have permission to delete these files.', 'danger')
        critical_error_logger(f"Deleting files was not allowed for {username}.")
        return redirect(url_for("maker_project.show_project_files", project_id=project_id))

### Download file route

@maker_project.route('/download-file/<int:file_id>')
@login_required
def download_file(file_id):
    # check if user is allowed to download this file
    user_project = UserProject.query.filter_by(user_id=current_user.id, project_id=File.query.get(file_id).project_id).first()
    permission = user_project.permission if user_project else "-"
    if "r" in permission:
        # Get file from db
        file = File.query.get(file_id)
        # Get path to project folder
        project_path = Project.query.get(file.project_id).path
        project_name = Project.query.get(file.project_id).project_name
        path_folder = os.path.join(os.getcwd(), project_path, project_name)    
        return send_from_directory(path_folder, file.filename, as_attachment=True, max_age=0)
    else:
        flash('You do not have permission to download this file.', 'danger')
        return redirect(url_for("maker_project.show_user_projects"))

### Rename file route

@maker_project.route('/rename-file/<int:file_id>', methods=['GET', 'POST'])
@login_required
def rename_file(file_id):
    form = RenameObject()
    file = File.query.get(file_id)
    project_id = file.project_id
    project = Project.query.get(project_id)
    file_name = file.filename
    username = current_user.username
    if form.validate_on_submit():
        # Get new name
        new_name = form.new_name.data
        # Check if this file name already exists for this project
        if File.query.filter_by(filename=new_name, project_id=project_id).first():
            flash(f'File {new_name} already exists. Please choose a different file name.', 'info')
            critical_error_logger(f'File {new_name} already exists.')
            return render_template("maker_project/rename-file.html", form=form, file_id=file_id, file_name=file.filename, project_id=project_id)
        # Check user permissions
        permission = UserProject.query.filter_by(user_id=current_user.id, project_id=project_id).first().permission
        # Get project details
        if "w" in permission:
            # Rename file
            old_path = os.path.join(os.getcwd(), project.path, project.project_name, file_name)
            new_path = os.path.join(os.getcwd(), project.path, project.project_name, new_name)
            try:
                os.rename(old_path, new_path)
                # Update file name in db
                file.filename = new_name
                db.session.commit()
                flash(f'File {file_name} renamed to {new_name} successfully.', 'success')
                current_app.logger.info(f"File {file_name} renamed to {new_name} by {username}.")
                return redirect(url_for("maker_project.show_project_files", project_id=project_id))
            except OSError as e:
                flash(f'An error occurred while renaming file {file_name}.', 'danger')
                critical_error_logger(f"Error renaming file {file_name} for {username}.")
                return redirect(url_for("maker_project.show_project_files", project_id=project_id))
        else:
            flash('You do not have permission to rename this file.', 'danger')
            critical_error_logger(f"Renaming file {file.filename} was not allowed for {username}.")
            return redirect(url_for("maker_project.show_project_files", project_id=project_id))
    else:
        # Check user permissions
        permission = UserProject.query.filter_by(user_id=current_user.id, project_id=project_id).first().permission
        if "w" in permission:
            return render_template("maker_project/rename-file.html", form=form, file_id=file_id, file_name=file_name, project_id=project_id)
        else:
            flash('You do not have permission to rename this file.', 'danger')
            critical_error_logger(f"Renaming file {file_name} was not allowed for {username}.")
            return redirect(url_for("maker_project.show_project_files", project_id=project_id))
        
#### MMM ROUTES

### MMM selection route

@maker_project.route('/mmm-selection/<int:project_id>', methods=['GET', 'POST'])
@login_required
def mmm_selection(project_id):
    form = MMMDynamicForm()
    # Empty HTML output for VerifyBibTeX step
    verifybibtex_html = ""
    if form.validate_on_submit():
        # Get selected files
        selected_files = [choice.file_name.data for choice in form.file_choices if choice.selected.data]
        # Get selected MMM step
        selected_mmm = form.mmm_choices.data
        # If XML2YAML is selected, get additional information
        xml2yaml_data: dict = get_xml2yaml_data(form) if selected_mmm == "xml2yaml" else dict()
        # Check if Zotero was used
        zotero_used = form.zotero_used.data
        # Create files
        project = Project.query.get(project_id)
        dir_path = os.path.join(project.path, project.project_name)
        # Check if an optional file name was passed for Maker/DW step
        custom_file_name = form.custom_file_name.data
        if custom_file_name != "":
            res_str = create_files(dir_path, selected_files, selected_mmm, project_id, xml2yaml_data, zotero_used, custom_file_name)
        else:
            res_str = create_files(dir_path, selected_files, selected_mmm, project_id, xml2yaml_data, zotero_used)
        # Create flash message depending on result
        if res_str == "true":
            # Create HTML output for VerifyBibTeX step
            if selected_mmm == "verifybibtex":
                verifybibtex_html = create_html_verifybibtex(dir_path)
            flash('Files created successfully!', 'success')
        else:
            flash(f'An error occurred while creating files: {res_str}', 'danger')
        # Debug rendering
        return render_template("maker_project/mmm-output.html", project_id=project_id, selected_files=selected_files, selected_mmm=selected_mmm, verifybibtex_html=verifybibtex_html)
    else:
        # Get all files and filenames from project folder
        files = File.query.filter_by(project_id=project_id).all()
        file_names = [f.filename for f in files]
        # Add files to form
        for file in file_names:
            file_form = form.file_choices.append_entry()
            file_form.selected.label.text = file  # Set the label to the file name
            file_form.file_name.data = file  # Store filename or identifier if needed
        return render_template("maker_project/mmm-selection.html", project_id=project_id, form=form)

