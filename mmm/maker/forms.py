from flask_wtf import FlaskForm
from flask_wtf.file import MultipleFileField, FileRequired, FileField
from wtforms import SubmitField, StringField, BooleanField, FieldList, FormField, RadioField, HiddenField
from wtforms.validators import DataRequired
from wtforms import ValidationError

class FileAllowed:
    '''Custom class to validate file extensions for FielField forms.
    '''
    def __init__(self, allowed_extensions, message=None):
        if not message:
            message = f"Allowed file types are: {', '.join(allowed_extensions)}"
        self.allowed_extensions = allowed_extensions
        self.message = message

    def __call__(self, form, field):
        if field.data:
            filename = field.data.filename
            if not ('.' in filename and filename.rsplit('.', 1)[1].lower() in self.allowed_extensions):
                raise ValidationError(self.message)

class Doc2MdForm(FlaskForm):
    file = FileField('Select DOC(X) or ODT files', validators=[FileRequired(), FileAllowed(["doc", "docx", "odt"])])
    zotero_used = BooleanField('Zotero used')
    submit = SubmitField('Convert to Markdown')

class VerifyBibTeXForm(FlaskForm):
    file = FileField('Select BibTeX file', validators=[FileRequired(), FileAllowed(["bib", "bibtex"])])
    submit = SubmitField('Verify BibTeX')

class XML2YAMLForm(FlaskForm):
    file = FileField('Select OJS-XML file', validators=[FileRequired(), FileAllowed(["xml"])])
    artnum = StringField('Article Number')
    volume_number = StringField('Volume Number')
    orcids = StringField('ORCIDs')
    year = StringField('Year')
    si_teaser = StringField('Special Issue Teaser')
    submit = SubmitField('Convert to YAML')

class Tex2PdfForm(FlaskForm):
    file = FileField('Select TeX file', validators=[FileRequired(), FileAllowed(["tex", "latex"])])
    images = MultipleFileField('Select images')
    submit = SubmitField('Convert to PDF')

class DWForm(FlaskForm):
    md_file = FileField('Select Markdown file', validators=[FileRequired(), FileAllowed(["md"])])
    bib_file = FileField('Select BibTeX file', validators=[FileRequired(), FileAllowed(["bib", "bibtex"])])
    yaml_file = FileField('Select YAML file', validators=[FileRequired(), FileAllowed(["yaml", "yml"])])
    image_files = MultipleFileField('Select image files')
    name = StringField('Article-Name')
    biblatex_used = BooleanField('BibLaTeX (beta)')
    compound_words_used = BooleanField('Compound-Words filter (beta)')
    submit = SubmitField('Create production files')