from flask_wtf import FlaskForm
from flask_wtf.file import MultipleFileField, FileRequired
from wtforms import SubmitField, StringField, BooleanField, FieldList, FormField, RadioField, HiddenField, SelectField
from wtforms.validators import DataRequired

class CreateProjectForm(FlaskForm):
    project_name = StringField('Project name', validators=[DataRequired()])
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
        ('doc2md', 'Create <b>Markdown</b> file from DOC(X) or ODT files (<b>DOC2MD</B>).'),
        ('verifybibtex', 'Check a <b>BibTeX file</b> for potential errors (<b>VerifyBibTeX</b>).'),
        ('xml2yaml', 'Create a <b>yaml metadata file</b> from OJS-XML (<b>XML2YAML</b>).'),
        ('dw', 'Create <b>production files</b> from yaml, bibtex, and markdown files (<b>Maker</b>).'),
        ('tex2pdf', 'Create a PDF from a <b>TeX file</b> (<b>TEX2PDF</b>).'),
    ], validators=[DataRequired()])
    # Additional information for XML2YAML:
    # volume_number: str, orcids: str, year: str, doi: str
    volume_number = StringField('Volume number')
    orcids = StringField('ORCIDs')
    year = StringField('Year')
    doi = StringField('DOI')
    submit = SubmitField('Create files')
    # Additional information for DOC2MD:
    zotero_used = BooleanField('Zotero used')
    # Additional possibility to create a custom file name for output files in Maker/DW step
    custom_file_name = StringField('Custom file name (optional)')
    # Select output format for MAKER step
    pdf_output = BooleanField('PDF')
    html_output = BooleanField('HTML')
    jats_output = BooleanField('JATS XML')
    tex_output = BooleanField('TeX') 
    
class RenameObject(FlaskForm):
    '''This form is used to rename a file or folder.'''
    new_name = StringField('New name', validators=[DataRequired()])
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