# Magic Manuscript Maker Web Application OS (Version 1.0.0)

## Introduction

This is the web application for the Magic Manuscript Maker (MMM) project. The MMM project is a tool that helps researchers to create manuscripts for scientific publications. The web application is a Flask-based web application that allows users to create projects, upload files, and share projects with other users.

The web application channels the four separate modules VerifyBibTeX-OS, XML2YAML-OS, DOC2MD-OS, and the Typesetting Container OS into a single web application. Consequently, when you want to use the web application, you need to make sure that the four modules are available as Docker containers.

## Installation
First, you need to have docker installed. Aftwards, download this repository and navigate to the root folder of the repository. Before you can run the web application, you need to check the `mmm.cfg` file. This file includes several variables that are needed to run the web application. The variables are as follows:

**General settings for the web application:**

- `UPLOAD_PATH`: The absolute path on the host system where the `upload` folder is found.
- `FLASK_ADMIN_USERNAME`: The username for the initial admin account.
- `FLASK_ADMIN_PASSWORD`: The password for the initial admin account.
- `SECRET_KEY`: The secret key for the Flask application.
- `DEBUG`: Whether to run the Flask application in debug mode.
- `SQLALCHEMY_DATABASE_URI`: The URI for the database.
- `LOG_FILE`: The path to the log file.
- `MAX_CONTENT_LENGTH`: The maximum content length for file uploads.

**Email settings:**

- `MAIL_SERVER`: The SMTP server for sending emails. Example: `smtp.gmail.com`.
- `MAIL_PORT`: The port of the SMTP server. Example: `587`.
- `MAIL_USERNAME`: The username for the SMTP server. 
- `MAIL_PASSWORD`: The password for the SMTP server.
- `MAIL_USE_TLS`: Whether to use TLS for the SMTP server. Example: `False` or `True`.
- `MAIL_USE_SSL`: Whether to use SSL for the SMTP server. Example: `False` or `True`.
- `MMM_MAIL_SUBJECT_PREFIX`: The subject prefix for emails. Example: `[MMM]`.	
- `MMM_MAIL_SENDER`: The sender of the emails (appears in the "From" field). Example: `Magic Manuscript Maker <info@email.com>`.

**Image names for the four modules:**

- `VERIFY_BIBTEX_IMAGE`: The image name for the VerifyBibTeX-OS module. Example: `ghcr.io/phimisci/verifybibtex-os:latest`
- `XML2YAML_IMAGE`: The image name for the XML2YAML-OS module. Example: `ghcr.io/phimisci/xml2yaml-os:latest`
- `DOC2MD_IMAGE`: The image name for the DOC2MD-OS module. Example: `ghcr.io/phimisci/doc2md-os:latest`
- `TYPESETTING_IMAGE`: The image name for the Typesetting Container OS module. Example: `ghcr.io/phimisci/typesetting-container-os:latest`	

Important note: Since some values such as `FLASK_ADMIN_USERNAME` and `FLASK_ADMIN_PASSWORD` are sensitive, you can use environment variables to set these values. If you do not want to use environment variables, you can set the values directly in the `mmm.cfg` file. In eithe case, the environment variables always have precedence over the values in the `mmm.cfg` file. The MMM currently checks the following environment variables:

- `FLASK_ADMIN_USERNAME`
- `FLASK_ADMIN_PASSWORD`
- `SECRET_KEY`

### logging
To enable logging, you need to mount two logfiles to the container (one for flask, the other for gunicorn). You can do this by adding `./flask-logging.log:/ap/flask-logging.log` and `./gunicorn-logging.log:/ap/gunicorn-logging.log` to the `docker run` command or `docker-compose.yml` file.

### Activate DB migrations
To activate the DB migrations, you need to run the following commands:
```bash
docker compose run mmm-app flask db init
docker compose run mmm-app flask db migrate -m "init migration"
docker compose run mmm-app flask db upgrade
```

This should create a `migrations` folder in the root folder including the migration files. Note that flask-migrate's update() function is run each time the container is started.

If the database schema has been updated, follow these steps:

1. Build new container that includes changed database schema (`docker-compose build`)
2. Run `docker compose mmm-app run flask db migrate -m "migration message"`
3. Start the container since update() should be run automatically-

## Usage

### Project

You can use the MMM-Web-App to create projects. A project is a collection of files and can be shared with other users (which need to have a MMM account already).

#### Create a project

1. Click on the `Projects` tab in the navigation bar.
2. Click on the `New project` link.
3. Give the project a name and click on "Create project".
4. If a project with this name does not exist already, the project is created and you are redirected to the project page where you should see the new project in the project list.

#### Download a project
There are three options to download a project:

1. Click on the `Download` button/icon next to the project in the project overview. This will download all project files as a zip file.
2. Click on the project name to open the project page. There you can click on the `Download` icon next to the user files and production files. This allows you to only download user or production files.

#### Rename a project
To rename a project, click on the "Edit" icon next to the project in the project overview. This will open another page where you can give your project a new name.

#### Project page
The project page of each project shows all files that belong to this project. Here, you can upload new files, delete files, download files, and rename files. Please note that the project page is only accessible to the project owner and users that the project has been shared with. You can also find an indication which access level you have. A project owner can grant you read, write, and delete permissions. For more information, see the "Share a project" section. Only files of certain types can be uploaded, and with a size not bigger than 25 MB.

#### Share a project
To share a project with another user, click on the "Sharing options" link on the project page. This will open a new page where you can select a user that has a MMM account from the database. You can now grant this user read, write, and delete permissions. Read permissions are automatically granted if you share a project with a user. Write and delete permissions need to be granted explicitly. You can also revoke all permissions from a user by checking the corresponding checkbox and clicking on the "Apply" button. Users who already have access to your project are marked with an asterisk (*). Users are informed via e-mail if a project is shared with them.

The permissions are as follows:

1. Read: The user can view the project and download files.
2. Write: The user can upload files to the project. The user can also delete files that they have uploaded.
3. Delete: The user can delete all files in the project.

Note that only the project owner can delete an entire project.

## Updates

### 0.3.4 (28.06.2024)

- Added a user settings menu where the user can change their password and email address
- Added an option to reset password
- Users are now informed via e-mail if project is shared with them
- Adding flask-migrate support for DB migrations

### 0.3.3 (31.05.2024)

- Only one flash message appears when deleting multiple files (2024/05/31)
- Maker-Selection/Maker step now highlights correct files in overview (2024/05/31)
- Fixed bug where invited user could not upload file with existing file with the same name in folder (2024/05/31)
- Permissions can now be updated; existing permissions are shown in the sharing options and checkboxes are checked for already granted permissions (2024/05/31)

### 0.3.2

- User/Production/All files can now be downloaded as a zip file (2024/05/16)
- Multiple files can be deleted (2024/05/16)
- An individual file name can now be passed to Maker/DW step (2024/05/16)
- Projects can now be shared with other users (2024/05/10)
- VerifyBibTeX now generates a HTML output, depending on the amount of issues found in the BibTeX-file (2024/05/10)
- If file is uploaded and the filename already exists, the *old* file is renamed to \<filename>_\<created_at>_\<random_string>.\<extension> (2024/05/02) 
- Files and projects can now be renamed (2024/05/02)