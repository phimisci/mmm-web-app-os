# Copyright (c) 2024 Thomas Jurczyk
# This software is provided under the MIT License.
# For more information, please refer to the LICENSE file in the root directory of this project.

import os, re
from typing import Union, Literal, List, Tuple, Optional
from mmm.maker_project.models import Project, File, UserProject
from mmm.maker_project.forms import MMMDynamicForm
from datetime import datetime
from mmm import db, mail
from flask_login import current_user
from flask import render_template, current_app
from datetime import datetime
import random, markdown2
from .file_creation_functions import create_files_doc2md, create_verifybibtex_report, create_files_xml2yaml, create_files_dw
from flask_mail import Message

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'doc', 'docx', 'yml', 'yaml', 'md', 'markdown', 'txt', 'tex', 'pdf', 'bib', 'bibtex', 'xml', 'odt'}

def allowed_file(filename: str) -> bool:
    '''Function to check if file extension is allowed.

        Arguments
        ---------

        filename : str
            Name of the file to be checked.

        Returns
        -------
        bool : True if file extension is allowed, False otherwise.
    '''
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_files(dir_path: str, selected_files: List[str], mmm_choice: str, project_id: int, xml2yaml_data: dict, zotero_used: bool, file_name: str, output_formats: List[Optional[str]] = []) -> str:
    '''Function to create files based on MMM-Project selections.

        Arguments
        ---------
        dir_path : str
            Path to the project folder.
        
        selected_files : List[str]
            The files that have been selected for the MMM processing.

        mmm_choice : str
            The selected MMM step. Can be doc2md, tex2pdf, verifybibtex, dw, xml2yaml.

        project_id : int
            The project ID necessary to register the produced files in DB.

        xml2yaml_data : dict
            Dictionary containing the data for XML2YAML (if this step was selected, else dict is empty).

        zotero_used : bool
            Boolean to indicate if Zotero was used (for DOC2MD step).

        file_name : Optional[str]
            Name of the file(s) to be created (for DW/Maker step).
        
        Returns
        -------
            str : "true" if everything was fine, else the problem that occurred as a string message.

    '''
    # Check if a file was selected
    if len(selected_files) == 0:
        return "Please select a file to proceed."
    # If file was selected, continue with Maker step selection
    if mmm_choice == "doc2md":
        doc = selected_files[0]
        # Check if file is doc(x) or odt
        if not doc.split(".")[-1].lower() in ["doc", "docx", "odt"]:
            return "Please pass a doc(x) or odt file to DOC2MD!"
        else:
            res = create_files_doc2md(dir_path, doc, zotero_used)
            if res:
                # Register files in DB
                # Currently produced files by DOC2MD: raw_markdown.md, clean_markdown.md, doc2md.log
                if os.path.exists(f"{os.getcwd()}/{dir_path}/raw_markdown.md"):
                    register_file_in_db("raw_markdown.md", project_id, True)
                if os.path.exists(f"{os.getcwd()}/{dir_path}/clean_markdown.md"):
                    register_file_in_db("clean_markdown.md", project_id, True)
                if os.path.exists(f"{os.getcwd()}/{dir_path}/doc2md.log"):
                    register_file_in_db("doc2md.log", project_id, True)
                if zotero_used:
                    # Check if bibliography.bib exists
                    if os.path.exists(f"{os.getcwd()}/{dir_path}/bibliography.bib"):
                        register_file_in_db("bibliography.bib", project_id, True)
                return "true"
            else:
                return "Error creating files using DOC2MD." 
    elif mmm_choice == "verifybibtex":
        bib = selected_files[0]
        # Check if file is bib or bibtex
        if not bib.split(".")[-1].lower() in ["bib", "bibtex"]:
            return "Please pass a bib or bibtex file to VERIFYBIBTEX!"
        else:
            # Create files
            res = create_verifybibtex_report(dir_path, bib)
            if res:
                # Currently produced files by VERIFYBIBTEX: bibtex-analysis-status-report.txt
                if os.path.exists(f"{os.getcwd()}/{dir_path}/verifybibtex-report.md"):
                    register_file_in_db("verifybibtex-report.md", project_id, True)
                return "true"
            else:
                return "Error creating files using VERIFYBIBTEX."
    elif mmm_choice == "xml2yaml":
        xml_file = selected_files[0]
        # Check if file is xml
        if not xml_file.split(".")[-1].lower() in ["xml"]:
            return "Please pass an xml file to XML2YAML!"
        res = create_files_xml2yaml(dir_path, xml_file, xml2yaml_data["volume_number"], xml2yaml_data["orcids"], xml2yaml_data["year"], xml2yaml_data["doi"])
        if res:
            # Currently produced files by XML2YAML: yaml-metadata.yaml
            if os.path.exists(f"{os.getcwd()}/{dir_path}/metadata.yaml"):
                register_file_in_db("metadata.yaml", project_id, True)
            return "true"
        else:
            return "Error creating files using XML2YAML."
    elif mmm_choice == "dw":
        # There shouldn't be more than 3 files selected for the typesetting step
        if len(selected_files) > 3:
            return "Please select only one YAML, Markdown, and BibTeX file to proceed with the typesetting module!"
        # Two files are mandatory: YAML, Markdown
        # One file is optional: BibTeX
        yaml_file = ""
        md_file = ""
        bib_file: Optional[str] = None # Optional
        for file in selected_files:
            # We only take the first yaml file, markdown file, and bib file
            if file.split(".")[-1].lower() in ["yaml", "yml"]:
                yaml_file = file
            elif file.split(".")[-1].lower() in ["md", "markdown"]:
                md_file = file
            elif file.split(".")[-1].lower() in ["bib", "bibtex"]:
                bib_file = file
        if yaml_file == "" or md_file == "":
            return "Please pass a YAML, Markdown, and BibTeX file to DW!"
        # Check if a file name was passed; if not use the name of the Markdown file
        if file_name == "":
            file_name = os.path.splitext(md_file)[0]
        # Proceed with creating files
        res = create_files_dw(dir_path, md_file, yaml_file, bibtex_file_name=bib_file, filename=file_name, output_formats=output_formats) if bib_file != None else create_files_dw(dir_path, md_file, yaml_file, filename=file_name, output_formats=output_formats)
        # Rename files back to original names if necessary
        if res:
            # Get file name from Markdown file if no file name was passed
            file_name = os.path.splitext(md_file)[0] if not file_name else file_name
            # Currently produced files by DW:
            if os.path.exists(f"{os.getcwd()}/{dir_path}/PROCESS.log"): 
                register_file_in_db("PROCESS.log", project_id, True)
            if os.path.exists(f"{os.getcwd()}/{dir_path}/{file_name}.pdf"):
                register_file_in_db(f"{file_name}.pdf", project_id, True)
            if os.path.exists(f"{os.getcwd()}/{dir_path}/{file_name}.html"):
                register_file_in_db(f"{file_name}.html", project_id, True)
            if os.path.exists(f"{os.getcwd()}/{dir_path}/{file_name}.jats"):
                register_file_in_db(f"{file_name}.jats", project_id, True)
            if os.path.exists(f"{os.getcwd()}/{dir_path}/{file_name}.tex"):
                register_file_in_db(f"{file_name}.tex", project_id, True)
            return "true"
        else:
            return "Error creating files using Maker."

def create_html_verifybibtex(dir_path: str) -> str:
    '''Function to create HTML file for VerifyBibTeX output.

        Parameters
        ---------
        dir_path : str
            Path to the project folder.

        Returns
        -------
        str : The HTML output for the corresponding bibtex-analysis-status-report.txt file in dir_path.
    '''
    # Check if bibtex-analysis-status-report.txt exists
    file_path = os.path.join(os.getcwd(), dir_path, "verifybibtex-report.md")
    if not os.path.exists(file_path):
        return ""
    # Read file
    with open(file_path, "r") as f:
        lines = f.readlines()
        # Clean data
        lines = [line.strip() for line in lines]
        lines = [line.lower() for line in lines if line != ""]
        # Create HTML output
        # First case: No errors
        if "found 0 errors." in lines:
            return "<p style='color: green;'>No errors found in the BibTeX file.</p>"
        # Second case: Manageable amount of errors found
        elif len(lines) < 100:
            f.seek(0)
            content = f.read()
            return markdown2.markdown(content)
        # Third case: Too many errors found
        else:
            return "<p style='color: red;'>Too many errors found in the BibTeX file. Please check the bibtex-analysis-status-report.txt file for details.</p>"

def create_new_project_func(project_name: str, username: str) -> Union[Literal[0],Literal[1]]:
    '''Function to create a new project folder in uploads/ if it doesn't exist.
    
            Arguments
            ---------
    
            project_name : str
                Name of the project to be created.
    
            username : str
                Username of the user creating the project.

            Returns
            -------
            int : 1 if project already exists, 0 if project was created successfully.
    '''
    # Replace spaces with underscores
    project_name = re.sub(r"\s+", "_", project_name)
    if not os.path.exists(f"uploads/{username}/{project_name}"):
        os.makedirs(f"uploads/{username}/{project_name}")
        # Register project in database
        register_project_in_db(f"uploads/{username}", project_name)
        # DEBUG: Create dummy file for testing; remove later
        with open(f"uploads/{username}/{project_name}/README.md", "w") as f:
            f.write("Read me.")
        # Register file in database
        current_project = Project.query.filter_by(path=f"uploads/{username}", project_name=project_name).first()
        project_id = current_project.id
        register_file_in_db("README.md", project_id, False)
        return 0
    else:
        return 1
    
def create_share_project_choices(user_id: int, project_id: int, user_name: str) -> Tuple[int, str]:
    '''Function to create user choices for sharing projects in project folder.

        Arguments
        ---------
        user_id : int
            User ID of the user for which projects should be shared.

        project_id : int
            ID of the project to be shared.
        
        user_name : str
            Username of the user with whom projects should be shared.

        Returns
        -------
        tuple : Tuple containing the user ID and the user name.
    '''
    # Check if this project is already shared with user
    # If this is the case, mark user with asterisk
    user_project = UserProject.query.filter_by(user_id=user_id, project_id=project_id).first()
    permissions = user_project.permission if user_project else None
    if user_project:
        return (user_id, user_name+f"*({permissions})")
    else:
        return (user_id, user_name)

def create_user_folder(username: str):
    '''Function to create user folder in upload if it doesn't exist.

        Arguments
        ---------

        username : str
            Username of the user for which folder is to be created.

        Returns
        -------
        None

    '''
    if not os.path.exists(f"uploads/{username}"):
        os.makedirs(f"uploads/{username}", exist_ok=True)
    
def delete_project_from_db(project_id: int):
    '''Function to delete project and all related files and user-project relations from database.

        Arguments
        ---------
        project_id : int
            ID of the project to be deleted.
        
        Returns
        -------
        None
    '''
    project = Project.query.get(project_id)
    # Get files from project
    files_from_project = File.query.filter_by(project_id=project_id).all()
    # Get user-project relations from project
    user_project_relations = UserProject.query.filter_by(project_id=project_id).all()
    # Delete project from database
    db.session.delete(project)
    # Delete files from database
    for file in files_from_project:
        db.session.delete(file)
    # Delete user-project relations from database
    for user_project in user_project_relations:
        db.session.delete(user_project)
    db.session.commit()

def file_exists(filename: str, project_id: int) -> str:
    '''Function to change filename of old file if file exists in database. 

        Arguments
        ---------

        filename : str
            Name of the file to be checked.
        project_id : int
            ID of the project to which file belongs.

        Returns
        -------
        None
    '''
    file = File.query.filter_by(filename=filename, project_id=project_id).first()
    if file:
        old_filename = filename
        found = False
        while not found:
            filename_list = filename.split(".")
            # Get date of old file and add it to new filename
            created_at = file.created_at
            created_at = created_at.strftime("%Y-%m-%d_%H-%M-%S")
            filename_list[0] = f"{filename_list[0]}_{created_at}_{str(random.randint(1, 10000))}"
            filename = ".".join(filename_list)
            # Check if file with the changed filename already exists in DB
            exists = File.query.filter_by(filename=filename, project_id=project_id).first()
            # If it does not exist, change filename of old file
            if not exists:
                # Change filename of old file in db
                file.filename = filename
                db.session.commit()
                # Change filename of old file in folder
                current_project = Project.query.get(project_id)
                # Get project path, which is particularly important if user who uploaded file is not the owner of the project
                project_path = current_project.path
                os.rename(f"{project_path}/{current_project.project_name}/{old_filename}", f"{project_path}//{current_project.project_name}/{filename}")
                found = True

def get_all_projects_for_user() -> Tuple[List[Project],List[Project]]:
    '''Function to get all projects for current user.

        Returns
        -------
        tuple of List[Project] : Tuple containing two lists: owned_projects and shared_projects.
        '''
    # Get all projects owned by user
    owned_projects = Project.query.join(UserProject).filter(UserProject.user_id == current_user.id, UserProject.creator==True).all()
    # Create list with projects shared with user
    shared_projects = Project.query.join(UserProject).filter(UserProject.user_id == current_user.id, UserProject.creator==False).all()
    return (owned_projects, shared_projects)

def get_xml2yaml_data(form: MMMDynamicForm) -> dict:
    '''Function to get XML2YAML data from form.

        Arguments
        ---------
        form : MMMDynamicForm
            Form containing the data.

        Returns
        -------
        dict
            Dictionary containing the data.
    '''
    data = {}
    data["volume_number"] = form.volume_number.data
    data["orcids"] = " ".join([orcid.strip() for orcid in form.orcids.data.split(";")]) if form.orcids.data != "" else None
    data["year"] = form.year.data
    data["doi"] = form.doi.data if form.doi.data != "" else None 
    return data

def register_file_in_db(filename: str, project_id: int, production_file: bool):
    '''Function to register a new file in project in database. If file already exists, do nothing.

        Arguments
        ---------
        filename : str
            Name of the file.

        project_id : int
            ID of the project.

        production_file : bool
            Boolean to indicate if file is a production file.

        Returns
        -------
        None
    '''
    file_exists = True if File.query.filter_by(filename=filename, project_id=project_id).all() != list() else False
    if not file_exists:
        # Check if file was produced by Maker steps and is thus a production file
        if production_file:
            new_file = File(filename, project_id, current_user.id, datetime.now(), datetime.now(), True, 0)
        else:
            new_file = File(filename, project_id, current_user.id, datetime.now(), datetime.now(), False, 0)
        db.session.add(new_file)
        db.session.commit()
    else:
        file = File.query.filter_by(filename=filename, project_id=project_id).first()
        # Switch to production file if necessary
        if production_file:
            file.production_file = True
        # Change last modified date
        file.changed_at = datetime.now()
        db.session.commit()

def register_project_in_db(path: str, project_name: str):
    '''Function to register a new project in database.

        Arguments
        ---------
        path : str
            Path of the project folder.

        project_name : str
            Name of the project.

        Returns
        -------
        None
    '''
    # Create new project in db
    new_project = Project(path, project_name, datetime.now(), datetime.now())
    db.session.add(new_project)
    db.session.commit()
    # Add project to current user
    current_project = Project.query.filter_by(path=path, project_name=project_name).first()
    project_id = current_project.id
    user_project = UserProject(current_user.id, project_id, "rwd", True)
    db.session.add(user_project)
    db.session.commit()

def send_email(to: str, subject: str, template: str, **kwargs):
    '''Function to send an email.

        Arguments
        ---------
        to : str
            Email address to which the email should be sent.

        subject : str
            Subject of the email.

        template : str
            Name of the template to be used for the email.

        **kwargs
            Keyword arguments to be passed to the template.

        Returns
        -------
        None
    '''
    msg = Message(current_app.config['MMM_MAIL_SUBJECT_PREFIX'] + subject,
                  sender=current_app.config['MMM_MAIL_SENDER'], recipients=[to])
    msg.body = render_template(f"maker_project/email/{template}.txt", **kwargs)
    #msg.html = render_template(f"email/{template}.txt", **kwargs)
    mail.send(msg)