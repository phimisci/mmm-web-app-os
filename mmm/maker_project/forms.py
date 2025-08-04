# Copyright (c) 2024 Thomas Jurczyk
# This software is provided under the MIT License.
# For more information, please refer to the LICENSE file in the root directory of this project.

from flask_wtf import FlaskForm
from flask_wtf.file import MultipleFileField, FileRequired
from wtforms import SubmitField, StringField, BooleanField, FieldList, FormField, RadioField, HiddenField, SelectField
from wtforms.validators import DataRequired, Regexp
import time

class CreateProjectForm(FlaskForm):
    project_name = StringField(
        "Project name", 
        validators=[DataRequired(),
                    Regexp(
                        regex="^[A-Za-z0-9_-]+$", 
                        message="Invalid name. Only characters (A-Z), numbers," \
                        " underscores and hyphens are allowed."
                        )
                    ]
        )
    submit = SubmitField('Create project')

class MMMChoiceForm(FlaskForm):
    """Form to render a single checkbox for files."""
    selected = BooleanField("Default")
    # The hidden field is used to store the file name and to pass this value to the MMM script.
    # This is a workaround since passing the value via BooleanField was not possible, see also FieldList docs:
    # "Note: Due to a limitation in how HTML sends values, FieldList cannot enclose BooleanField or SubmitField instances."
    # https://wtforms.readthedocs.io/en/2.3.x/fields/#wtforms.fields.FieldList
    file_name = HiddenField()

class MMMDynamicForm(FlaskForm):
    """Dynamic form to add checkboxes depending on files in project folder."""
    file_choices = FieldList(FormField(MMMChoiceForm))
    # Form for the main MMM choice
    mmm_choices = RadioField('Select a Maker step', choices=[
        ('doc2md', '1. Create <b>Markdown</b> file from DOC(X) or ODT files (<b>DOC2MD</B>).'),
        ('verifybibtex', '2. Check a <b>BibTeX file</b> for potential errors (<b>VerifyBibTeX</b>).'),
        ('xml2yaml', '3. Create a <b>YAML metadata file</b> from OJS-XML (<b>XML2YAML</b>).'),
        ('dw', '4. Create <b>production files</b> from YAML, BibTeX, and Markdown files (<b>Maker</b>).'),
        ('tex2pdf', '5. Optional step: Create a <b>PDF</b> from a TeX file (<b>TEX2PDF</b>).'),
    ], validators=[DataRequired()])
    # Additional information for XML2YAML:
    # volume_number: str, orcids: str, year: str, doi: str
    volume_number = StringField(
        'Volume number', 
        default=str(int(time.strftime("%Y")) - 2019)
        )
    orcids = StringField('ORCIDs')
    year = StringField('Year', default=time.strftime("%Y"))
    doi = StringField('DOI')
    issue_info = RadioField('Is this a standalone article?', choices=[
        ('standalone', 'This is a standalone article'),
        ('symposium', 'This article is part of a book symposium'),
        ('specialissue', 'This article is part of a special issue')
    ], default='standalone', validators=[DataRequired()])
    special_issue = StringField('Special Issue Teaser')
    special_issue_title = StringField(
        'Title of Special Issue/Title of discussed book'
        )
    special_issue_book_authors = StringField(
        'Author(s) of discussed book (separated by ;)', 
        default='Author 1; Author 2'
        )
    special_issue_editors = StringField(
        'Editors of Special Issue/Book Symposium',
        default='Editor 1; Editor 2'
        )
    submit = SubmitField('Create files')
    # Additional information for DOC2MD:
    zotero_used = BooleanField('Zotero used')
    bibliography_choices = RadioField('Select bibliography processing', choices=[
        ('none', 'No external processing'),
        ('zotero', 'Zotero was used inside Word'),
        ('auto', 'Auto-encode citations based on bibliography file')
    ], default='none', validators=[DataRequired()])
    # Additional possibility to create a custom file name for output files in Maker/DW step
    custom_file_name = StringField('Custom file name (optional)')
    # Select output format for MAKER step
    layout_version = SelectField('Select the layout version', 
                                 choices=[
                                     ('classic', 'Classic (2019-2025)'),
                                     ('twocolumn', 'Twocolumn (2025-)')
                                 ],
                                 validators=[DataRequired()]
                                 )
    compound_filter = BooleanField('Use a filter to process compound words')
    manual_parentheses = BooleanField('The citation were auto-encoded in ' \
                                      'the DOC2MD step.')
    pdf_output = BooleanField('PDF')
    html_output = BooleanField('HTML')
    jats_output = BooleanField('JATS XML')
    tex_output = BooleanField('TeX') 
    proof_output = BooleanField('PROOF')
    
class RenameObject(FlaskForm):
    '''This form is used to rename a file or folder.'''
    new_name = StringField(
        'New name', 
        validators=[DataRequired(),
                    Regexp(
                        regex="^[A-Za-z0-9_-]+$", 
                        message="Invalid name. Only characters (A-Z), numbers," \
                        " underscores and hyphens are allowed."
                        )]
        )
    submit = SubmitField('Rename')

class ShareProjectWithUser(FlaskForm):
    '''This form is used to share a project with a user.'''
    user = SelectField('User', coerce=int, validators=[DataRequired()])
    write_permission = BooleanField('Write permission')
    delete_permission = BooleanField('Delete permission')
    revoke_permission = BooleanField('Revoke project access')
    submit = SubmitField('Apply')

class UploadForm(FlaskForm):
    files = MultipleFileField('Select files', validators=[FileRequired()])
    submit = SubmitField('Upload')
