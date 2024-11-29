import string, os, random, subprocess, zipfile
from datetime import datetime
from typing import List
from flask import current_app
from flask_login import current_user
import shutil
from flask import current_app

def create_files_doc2md(dir_path: str, doc_file_name: str, zotero_used: bool) -> bool:
    '''Function to call Docker container to create MD files from uploaded document file.

        Parameters
        ----------
            dir_path: str
                The path to the directory where the uploaded files are stored.
            doc_file_name: str
                The name of the document file (needs to be in dir_path; doc|docx|odt).
            zotero_used: bool
                Indicate whether Zotero was used to create the document file.
        Returns
        -------
            bool: True if the file has successfully been created, else False.
    '''

    ## DIFFICULT PART!
    ## This program uses docker in docker. When calling the original docker run --rm --volume "$(pwd):/app/article" --user $(id -u):$(id -g) registry.git.noc.ruhr-uni-bochum.de/phimisci/phimisci-typesetting-container/0.0.1:latest <METADATA>.yaml <ARTICLE>.md
    ## we need to make sure to mount the correct volume from the HOST system; to make sure this is the case, you NEED to pass this path explicitly in an environment variable when creating the container (UPLOAD_PATH in this example)

    HOST_UPLOAD_DIR = os.path.join(current_app.config.get('UPLOAD_PATH'), dir_path)

    # Run docker container
    if not zotero_used:
        docker_command = ["docker", "run","--rm", "--volume", f"{HOST_UPLOAD_DIR}:/app/files", current_app.config.get('DOC2MD_IMAGE'), doc_file_name]
    else:
        docker_command = ["docker", "run","--rm", "--volume", f"{HOST_UPLOAD_DIR}:/app/files", current_app.config.get('DOC2MD_IMAGE'), "--zotero", doc_file_name]

    result = subprocess.run(docker_command)
    
    # check if the command was successful
    if result.returncode == 0:
        docker_logger_success("DOC2MD", dir_path)
        print("Container started successfully")
        return True
    else:
        docker_logger_error("DOC2MD", dir_path)
        print("Error in running container")
        return False

def create_files_dw(dir_path: str, md_file_name: str, yml_file_name: str, bibtex_file_name: str = "default", biblatex: bool = False, compound: bool = False) -> bool:
    '''Function to call Docker container to create output files from uploaded files.

        Parameters
        ----------
            dir_path: str
                The path to the directory where the uploaded files are stored.

            md_file_name: str
                The name of the markdown file (needs to be in dir_path).

            yml_file_name: str
                The name of the yaml file (needs to be in dir_path).

            bibtex_file_name: str
                The name of the bibtex file (needs to be in dir_path). Only need to be passed if it differs from md_file_name.

            biblatex: bool
                Indicate whether BibLaTeX should be used instead of citeproc.

            compound: bool
                Indicate whether the article should use compound-word filter (replacing -- with \\babelhypen{hard}).

        Returns
        -------
            bool: True if the file has successfully been created, else False.
    '''


    ## check bibtex file
    ## if bibtex_file_name is not default, we need to check if the file exists
    ## and create a copy of it with the same name as the md file
    ## this is necessary because the container expects the bibtex file to have the same name as the md file
    if bibtex_file_name != "default":
        bibtex_file_path = os.path.join("/app", dir_path, bibtex_file_name)
        if not os.path.exists(bibtex_file_path):
            print("BIBTEX FILE NOT FOUND")
            docker_logger_error("MAKER", "Could not find BibTeX file.")
            return False
        # we need to create a copy of bibtex file with new name
        # get file name without extension
        md_file_name_no_extension = os.path.splitext(md_file_name)[0]
        bib_file_name_no_extension = os.path.splitext(bibtex_file_name)[0]
        if md_file_name_no_extension != bib_file_name_no_extension:
            shutil.copy(bibtex_file_path, os.path.join("/app", dir_path, f"{md_file_name_no_extension}.bib"))
        
    ## DIFFICULT PART!
    ## This program uses docker in docker. When calling the original docker run --rm --volume "$(pwd):/app/article" --user $(id -u):$(id -g) registry.git.noc.ruhr-uni-bochum.de/phimisci/phimisci-typesetting-container/0.0.1:latest <METADATA>.yaml <ARTICLE>.md
    ## we need to make sure to mount the correct volume from the HOST system; to make sure this is the case, you NEED to pass this path explicitly in an environment variable when creating the container (UPLOAD_PATH in this example)

    HOST_UPLOAD_DIR = os.path.join(current_app.config.get('UPLOAD_PATH'), dir_path) # TODO: use pathlib

    # docker run --rm --volume "$(pwd):/app/article" --user $(id -u):$(id -g) registry.git.noc.ruhr-uni-bochum.de/phimisci/phimisci-typesetting-container/0.0.1:latest <METADATA>.yaml <ARTICLE>.md
    docker_command = ["docker", "run","--rm", "--volume", f"{HOST_UPLOAD_DIR}:/app/article", current_app.config.get('TYPESETTING_IMAGE'), yml_file_name, md_file_name]

    ## adding additional optional arguments
    ### biblatex
    if biblatex == True:
        print("BIBLATEX")
        docker_command.extend(["--biblatex"])
    ### compound
    if compound == True:
        print("COMPOUND")
        docker_command.extend(["--compound"])
  
    result = subprocess.run(docker_command)
    
    # check if the command was successful
    if result.returncode == 0:
        docker_logger_success("MAKER", dir_path)
        print("Container started successfully")
        return True
    else:
        docker_logger_error("MAKER", dir_path)
        print("Error in running container")
        return False

def create_files_tex2pdf(dir_path: str, tex_file_name: str) -> bool:
    '''Function to call Docker container to create PDF file from uploaded TeX file.

        Parameters
        ----------
            dir_path: str
                The path to the directory where the uploaded files are stored.
                
            tex_file_name: str
                The name of the TeX file (needs to be in dir_path).
        
        Returns
        -------
            bool: True if the file has successfully been created, else False.
    '''

    ## DIFFICULT PART!
    ## This program uses docker in docker. When calling the original docker run --rm --volume "$(pwd):/app/article" --user $(id -u):$(id -g) registry.git.noc.ruhr-uni-bochum.de/phimisci/phimisci-typesetting-container/0.0.1:latest <METADATA>.yaml <ARTICLE>.md
    ## we need to make sure to mount the correct volume from the HOST system; to make sure this is the case, you NEED to pass this path explicitly in an environment variable when creating the container (UPLOAD_PATH in this example)

    HOST_UPLOAD_DIR = os.path.join(current_app.config.get('UPLOAD_PATH'), dir_path) # TODO: use pathlib

    # docker run --rm --volume "$(pwd):/app/article" --user $(id -u):$(id -g) registry.git.noc.ruhr-uni-bochum.de/phimisci/phimisci-typesetting-container/0.0.1:latest <METADATA>.yaml <ARTICLE>.md
    docker_command = ["docker", "run","--rm", "-v", f"{HOST_UPLOAD_DIR}:/app/output", "-v", f"{HOST_UPLOAD_DIR}/{tex_file_name}:/app/{tex_file_name}", "-v", f"{HOST_UPLOAD_DIR}/article:/app/article" , "registry.git.noc.ruhr-uni-bochum.de/phimisci/tex2pdf/0.0.2:latest", tex_file_name]
    
    result = subprocess.run(docker_command)
    
    # check if the command was successful
    if result.returncode == 0:
        docker_logger_success("TEX2PDF", dir_path)
        print("Container started successfully")
        return True
    else:
        docker_logger_error("TEX2PDF", dir_path)
        print("Error in running container")
        return False

def create_files_xml2yaml(dir_path: str, xml_file_name: str, volume_number: str, orcids: str, year: str, doi: str) -> bool:
    '''Function to call Docker container to create metadata.yaml file from uploaded OJS-XML.

        Parameters
        ----------
            dir_path: str
                The path to the directory where the uploaded XML is stored.
            xml_file_name: str
                The name of the XML file (needs to be in dir_path).
            argument_string: str
                The additional arguments for the XML2YAML container (year, volume, doi etc.).

        Returns
        -------
            bool: True if the file has successfully been created, else False.
    '''

    ## DIFFICULT PART!
    ## This program uses docker in docker. When calling the original docker container
    ## we need to make sure to mount the correct volume from the HOST system; to make sure this is the case, you NEED to pass this path explicitly in an environment variable or the mmm.cfg when creating the container (UPLOAD_PATH must exist on the HOST)

    HOST_UPLOAD_DIR = os.path.join(current_app.config.get('UPLOAD_PATH'), dir_path) # TODO: use pathlib
    ABS_FILE_PATH = os.path.join(HOST_UPLOAD_DIR, xml_file_name)

    # Docker command for XML2YAML-OS
    # See https://github.com/phimisci/xml2yaml-os
    docker_command = ["docker", "run","--rm", "--volume", f"{ABS_FILE_PATH}:/app/xml_input/{xml_file_name}" ,"--volume", f"{HOST_UPLOAD_DIR}:/app/yaml_output", current_app.config.get('XML2YAML_IMAGE'), xml_file_name]

    ## Adding additional optional arguments
    ## These arguments are depend on the configuration of XML2YAML-OS
    ### Year
    if year != "":
        docker_command.extend(["--year", year])
    ### Volume
    if volume_number != "":
        docker_command.extend(["--volume", volume_number])
    ### ORCIDs
    if orcids != None:
        docker_command.extend(["--orcid", orcids])
    ### DOI
    if doi != None:
        docker_command.extend(["--doi", f'{doi}'])

    # running docker container
    result = subprocess.run(docker_command)

    # check if the command was successful
    if result.returncode == 0:
        docker_logger_success("XML2YAML", dir_path)
        print("Container started successfully")
        return True
    else:
        docker_logger_error("XML2YAML", dir_path)
        print("Error in running container")
        return False

def create_verifybibtex_report(dir_path: str, bibtex_file: str = "bib.bib") -> bool:
    """Function to call VerifyBibTeX Docker container to create .yaml file from uploaded BibTeX file.

    Parameters
    ----------
    dir_path : str
        The path to the directory where the uploaded files are stored.

    bibtex_file : str
        The name of the BibTeX file (needs to be in dir_path).

    Returns
    -------
    bool
        Indicate whether report was successfully created.
    """    

    ## DIFFICULT PART!
    ## This program uses docker in docker. When calling the original docker container
    ## we need to make sure to mount the correct volume from the HOST system; to make sure this is the case, you NEED to pass this path explicitly in an environment variable when creating the container (UPLOAD_PATH in this example that NEEDS to exist on the HOST)

    HOST_UPLOAD_DIR = os.path.join(current_app.config.get('UPLOAD_PATH'), dir_path) # TODO: use pathlib

    # Run docker container
    docker_command = ["docker", "run","--rm", "-e", f"BIBTEX_FILE={bibtex_file}", "--volume", f"{HOST_UPLOAD_DIR}:/app/report", current_app.config.get('VERIFYBIBTEX_IMAGE')]

    # Running docker container
    result = subprocess.run(docker_command)

    # Check if the command was successful
    if result.returncode == 0:
        docker_logger_success("VERIFYBIBTEX", dir_path)
        print("Container started successfully")
        return True
    else:
        docker_logger_error("VERIFYBIBTEX", dir_path)
        print("Error in running container")
        return False

def create_upload_directory():
    '''Function to create a upload directory in uploads/.

        Returns
        -------
            str: Path to the upload directory.
    '''
    ## create new unique directory for this upload first
    dir_name_exists = True
    while dir_name_exists:
        dir_name = "uploads/"+generate_random_dir_name()
        if not os.path.exists(dir_name):
            dir_name_exists = False
    os.makedirs(dir_name, exist_ok=True)
    print(f"{dir_name} created!")
    return dir_name

def create_zip_file(dir_path: str, file_list: List[str]) -> None:
    '''Function to create a zip file i dir_path with all files in that folder.
    '''
    initial_dir = os.getcwd()
    ZIP_FILENAME = "article_data_phimisci.zip"
    print(f"Created {ZIP_FILENAME}")
    os.chdir(dir_path)
    with zipfile.ZipFile(ZIP_FILENAME, "w") as zip_file:
        for file in file_list:
            zip_file.write(file)
    os.chdir(initial_dir)

def generate_random_dir_name(length=10):
    '''Function to generate unique directory name for uploads (random string).
    '''
    # combine ASCII letters and digits
    characters = string.ascii_letters + string.digits
    # get the current date
    current_date = datetime.now()
    # format the date as a string in the format "Year-Month-Day"
    formatted_date = current_date.strftime("%Y-%m-%d")
    return ''.join(random.choice(characters) for i in range(length))+f"_{formatted_date}"

### LOGGER FUNCTIONS

def docker_logger_success(container_name: str, folder_path: str) -> None:
    """
    Logs a success message with the container name, username, and folder path.

    Parameters:
        container_name (str): The name of the Docker container.
        folder_path (str): The path of the folder where the files were created.
    """
    username: str = current_user.username if current_user.is_authenticated else "Anonymous"
    current_app.logger.info(f"{container_name} ran successfully by {username}. Files were created in folder {folder_path}")

def docker_logger_error(container_name: str, folder_path: str) -> None:
    """
    Logs a fail message indicating that a container crashed during execution.

    Parameters:
        container_name (str): The name of the Docker container.
        folder_path (str): The path of the folder where the files were created.
    """
    username: str = current_user.username if current_user.is_authenticated else "Anonymous"
    current_app.logger.info(f"{container_name} crashed when used by {username}. File folder has been created at {folder_path}")

def critical_error_logger(error_message: str) -> None:
    """
    Logs a critical error message.

    Parameters:
        error_message (str): The error message to be logged.
    """
    username: str = current_user.username if current_user.is_authenticated else "Anonymous"
    current_app.logger.critical(f"User {username} caused a critical error: {error_message}")