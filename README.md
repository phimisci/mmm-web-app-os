# Magic Manuscript Maker Web Application OS (Version 1.0.0)

This is the PhiMiSci version of the Magic Manuscript Maker Web Application.

## Introduction
The Magic Manuscript Maker is a tool that helps publishers to create manuscripts for scientific publications. The Flask-based web application allows users to create projects, upload files, and share projects with other users. The Magic Manuscript Maker was built using Flask and Docker. Even though it comes with default templates and settings, it is highly customizable and can be extended to fit your needs. The web application can either be run locally or deployed to a server.

The web application channels five separate modules into a single source publishing workflow with Pandoc:

1. DOC2MD-OS: Converting DOCX files (with Zotero citations) into Markdown and BibTeX files.
2. VerifyBibTeX-OS: Check the BibTeX file for potential problems.
3. XML2YAML-OS: Transform OJS-XML into a suitable metadata.yaml file that can be used along with the Markdown file to create the final publications.
4. Typesetting Container OS: Render the article into the desired format (e.g., PDF, HTML, TEX, JATS).

Please bear in mind that the web application is still in development and may contain bugs. If you encounter any issues, please report them in the issue tracker. Also, the web application is designed for smaller teams and not for large-scale use. The user system works by invitation only, and the web application does not support self-registration. This means that an initial admin account is automatically created when the web application is started for the first time. The admin account can then invite other users to the web application.

## Installation
First, you need to have docker installed. Afterwards, download this repository and navigate to the root folder of the repository. Before you can run the web application, you need to create a `mmm.cfg` file that includes important information to run the application. To start, you can copy the text below and adjust the values to your needs:

```bash
# General settings
SECRET_KEY = '10asdw2329+~abhpi2514b79a@+ep+ponhj8i4@_ij*@x@' # Can and should be set via environment variable
DEBUG = False # Can be set via environment variable
SQLALCHEMY_DATABASE_URI = 'postgresql://admin:admin@postgres:5432/mmm-database' # Link to the database, should usually run in a separate container
LOG_FILE = 'flask-logging.log' # Can be set via environment variable
MAX_CONTENT_LENGTH = 32 * 1024 * 1024 # Maximum file size for uploads (32 MB)
UPLOAD_PATH = '/path/to/root/folder/mmm' # This is important and should include the absolute path on the host system to the folder where this repository is located; can be set via environment variable
# Mail settings
# The mail server settings are used to send e-mails to users when they are invited to the web application or want to change their passwords
MAIL_SERVER = 'webhost.mailing.com' # Can be set via environment variable
MAIL_USERNAME = 'mmmadmin' # Can be set via environment variable
MAIL_PORT = 587 # Can be set via environment variable
MAIL_USE_TLS = True # Can be set via environment variable
MAIL_USE_SSL = False # Can be set via environment variable
MAIL_PASSWORD = 'password' # Can be set via environment variable
MMM_MAIL_SUBJECT_PREFIX = '[MMM] ' # Non-sensitive value, cannot be set via environment variable
MMM_MAIL_SENDER = 'MMM Admin <info@mmm.org>' # Non-sensitive value, cannot be set via environment variable
# Module images
# These are the images that are used to run the different modules. You can set these values via environment variables
# We highly recommend using the images provided by the Philosophy and the Mind Sciences team and not to change these values
VERIFYBIBTEX_IMAGE = 'ghcr.io/phimisci/verifybibtex-os:latest' # Can be set via environment variable
XML2YAML_IMAGE = 'ghcr.io/phimisci/xml2yaml-os:latest' # Can be set via environment variable
DOC2MD_IMAGE = 'ghcr.io/phimisci/doc2md-os:latest' # Can be set via environment variable
TYPESETTING_IMAGE = 'ghcr.io/phimisci/typesetting-container-os:latest' # Can be set via environment variable
TEX2PDF_IMAGE = 'ghcr.io/phimisci/tex2pdf-os:latest' # Can be set via environment variable
```

Important note: Since some values such as `FLASK_ADMIN_USERNAME` and `FLASK_ADMIN_PASSWORD` are sensitive, you can use environment variables to set these values. The environment variables always have precedence over the values in the `mmm.cfg` file. The `mmm.cfg` file is handy for local use and for non-sensitive values.

After you have created the `mmm.cfg` file, you can start the web application by running the following command, we recommend creating a docker-compose.yml file to make the process easier. Here is an example of a `docker-compose.yml` file, where we use a PostgreSQL database (of course, you can also use a lightweight SQLite database, which would make the setup even easier):

```yaml
services:
  mmm-app: 
    build: .
    ports:
      - "127.0.0.1:8500:8500"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock  # Mount Docker socket, very important for the modules!
      - ./uploads:/app/uploads
      - ./db:/app/db
      - ./flask-logging.log:/app/flask-logging.log
      - ./mmm.cfg:/app/mmm.cfg
      - ./migrations:/app/migrations
    environment:
      - FLASK_ADMIN_USERNAME=new-admin # Feel free to add as many environment variables as you like
    stdin_open: true
    tty: true

  postgres: # You only need this service if you want to use a PostgreSQL database
    image: postgres:13
    environment:
      - POSTGRES_USER=admin
      - POSTGRES_PASSWORD=admin
      - POSTGRES_DB=mmm-database
    ports:
      - "5432:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data

volumes:
  postgres-data:
```

After you have created the `docker-compose.yml` file, you can build the container by running the following command: `docker-compose build`. After the container has been built, you can start the container by running the following command: `docker-compose up`. The web application should now be accessible at `http://localhost:8500`. An important note: If you haven't pulled the images for the modules yet, the container will automatically pull the images from the Docker Hub. This can take some time, depending on your internet connection. However, the images are only pulled once and are then stored on your system, so you don't have to pull them again.

Note that the web application currently uses Docker-in-Docker (DinD) to run the modules. This means that the web application can start and stop containers. This is necessary because the modules are run in separate containers. The conainer uses the docker daemon on the host system to start the containers. This is why you need to mount the Docker socket (`/var/run/docker.sock`) to the container.

## Logging
To enable logging, you need to mount a logfile to the container. You can do this by adding `./flask-logging.log:/app/flask-logging.log` to the `docker-compose.yml` file.

## Activate DB migrations
To activate the DB migrations, you need to run the following commands:

```bash
docker compose run mmm-app flask db init
docker compose run mmm-app flask db migrate -m "init migration"
docker compose run mmm-app flask db upgrade
```

This should create a `migrations` folder in the root folder including the migration files. Note that flask-migrate's `update()` function is run each time the container is started.

If the database schema has been updated, follow these steps:

1. Build new container that includes changed database schema (`docker-compose build`)
2. Run `docker compose mmm-app run flask db migrate -m "migration message"`
3. Start the container since `update()` should be run automatically.

## Usage

### User system

The user system is based on invitations. This means that an admin user, which is created by default when first setting up the container, must create accounts for others users using the admin menu in the webinterface. All users can change their passwords, set new email addresses, and request a new password if they have forgoetten their password. In order for this to work, you need to set up the mail server settings in the `mmm.cfg` file or via environment variables. 

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
The project page of each project shows all files that belong to this project. Here, you can upload new files, delete files, download files, and rename files. Please note that the project page is only accessible to the project owner and users that the project has been shared with. You can also find an indication which access level you have. A project owner can grant you read, write, and delete permissions. For more information, see the "Share a project" section. Only files of certain types can be uploaded, and with a size not bigger than 32 MB.

#### Share a project
To share a project with another user, click on the "Sharing options" link on the project page. This will open a new page where you can select a user that has a MMM account from the database. You can now grant this user read, write, and delete permissions. Read permissions are automatically granted if you share a project with a user. Write and delete permissions need to be granted explicitly. You can also revoke all permissions from a user by checking the corresponding checkbox and clicking on the "Apply" button. Users who already have access to your project are marked with an asterisk (*). Users are informed via e-mail if a project is shared with them.

The permissions are as follows:

1. Read: The user can view the project and download files.
2. Write: The user can upload files to the project. The user can also delete files that they have uploaded.
3. Delete: The user can delete all files in the project.

Note that only the project owner can delete an entire project. If the email settins are set up correctly, users are informed via email if a project is shared with them.

## About
This application was developed by Thomas Jurczyk ([thomjur](https://github.com/thomjur) on GitHub) for the journal [Philosophy and the Mind Sciences](https://philosophymindscience.org/) as part of a project funded by the German Research Foundation (DFG).

## Versions

### Version 1.0.0

- Initial release

