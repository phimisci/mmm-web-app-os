import os
from flask import request, render_template, send_from_directory
from mmm.maker.tools import create_upload_directory, create_files_dw, create_zip_file, create_files_xml2yaml, create_verifybibtex_report, create_files_tex2pdf, create_files_doc2md, critical_error_logger
from . import maker
from flask_login import login_required
from .forms import Doc2MdForm, VerifyBibTeXForm, XML2YAMLForm, Tex2PdfForm, DWForm

## MAKER INDEX ROUTE
@maker.route("/", methods=['GET'])
@login_required
def index():
    if request.method == "GET":
        return render_template("maker/index.html")

## DOC2MD ROUTES
@maker.route("/doc2md", methods=['GET', 'POST'])
@login_required
def doc2md():
    form = Doc2MdForm()
    if form.validate_on_submit():
        # Create new upload directory in uploads/
        dir_path = create_upload_directory()
        # Retrieve & save all files uploaded by the user
        doc_file_name = form.file.data.filename
        ## Save DOC(X) or ODT files
        form.file.data.save(f"{dir_path}/{doc_file_name}")
        # Check if Zotero was used to create citations
        zotero_used = form.zotero_used.data
        ## Create raw_markdown.md and clean_markdown.md using doc2md docker-container
        res = create_files_doc2md(dir_path, doc_file_name, zotero_used)
        if res:
            file_list = os.listdir(dir_path)
            return render_template("maker/doc2md_output.html", dir_path=dir_path, file_list=file_list)
        else:
            critical_error_logger("DOC2MD: Error rendering files.")
            return render_template("500.html")
    else:
        return render_template("maker/doc2md.html", form=form)

## TEX2PDF ROUTES
@maker.route("/tex2pdf", methods=['GET', 'POST'])
@login_required
def tex2pdf():
    form = Tex2PdfForm()
    if form.validate_on_submit():
        # Create new upload directory in uploads/
        dir_path = create_upload_directory()
        # create subfolder for images
        os.makedirs(f"{dir_path}/article", exist_ok=True)
        # Save TeX file
        form.file.data.save(f"{dir_path}/{form.file.data.filename}")
        tex_file_name = form.file.data.filename
        # Save images in article subfolder
        if form.images.data:
            for file in form.images.data:
                file.save(f"{dir_path}/article/{file.filename}")
        res = create_files_tex2pdf(dir_path, tex_file_name)
        if res:
            pdf_file_name = tex_file_name.split(".")[0]+".pdf"
            log_file_name = tex_file_name.split(".")[0]+".log"
            return render_template("maker/tex2pdf_output.html", dir_path=dir_path, pdf_file_name=pdf_file_name, log_file_name=log_file_name)
        else:
            critical_error_logger("TEX2PDF: Error rendering files.")
            return render_template("500.html")
    else:
        return render_template("maker/tex2pdf.html", form=form)
        
## XML2YAML ROUTES
@maker.route("/xml2yaml", methods=['GET', 'POST'])
@login_required
def xml2yaml():
    form = XML2YAMLForm()
    if form.validate_on_submit():
        # Create new upload directory in uploads/
        dir_path = create_upload_directory()
        # Save XML file
        xml_file_name = form.file.data.filename
        form.file.data.save(f"{dir_path}/{xml_file_name}")
        # Parse rest of form dara
        volume_number = form.volume_number.data
        artnum = form.artnum.data
        year = form.year.data
        # clumsy way to transform: Jurczyk=0000-0002-5943-2305; Wiese=0000-0003-3338-7398 -> Jurczyk=0000-0002-5943-2305 Wiese=0000-0003-3338-7398
        orcids = form.orcids.data
        orcids = " ".join([orcid.strip() for orcid in orcids.split(";")]) if orcids != "" else None
        si_teaser = form.si_teaser.data if form.si_teaser.data != "" else None
        res = create_files_xml2yaml(dir_path, xml_file_name, artnum, volume_number, orcids, year, si_teaser)
        if res:
            return render_template("maker/xml2yaml_output.html", dir_path=dir_path)
        else:
            critical_error_logger("XML2YAML: Error rendering files.")
            return render_template("500.html")
    else:
        return render_template("maker/xml2yaml.html", form=form)

## VerifyBibTeX ROUTES
@maker.route("/verifybibtex", methods=['GET', 'POST'])
@login_required
def verifybibtex():
    form = VerifyBibTeXForm()
    if form.validate_on_submit():
        # Create new upload directory in uploads/
        dir_path = create_upload_directory()
        # Retrieve & save all files uploaded by the user
        ## Save BibTeX file
        form.file.data.save(f"{dir_path}/bib.bib")
        ## Create bibtex-analysis-status-report.txt using verifybibtex docker-container
        res = create_verifybibtex_report(dir_path)
        if res:
            return render_template("maker/verifybibtex_output.html", dir_path=dir_path)
        else:
            critical_error_logger("VerifyBibTeX: Error checking BibTeX file.")
            return render_template("500.html")
    else:
        return render_template("maker/verifybibtex.html", form=form)

## DW ROUTES
@maker.route("/dw", methods=['GET', 'POST'])
@login_required
def dw():
    form = DWForm()
    if form.validate_on_submit():
        # Create new upload directory in uploads/
        dir_path = create_upload_directory()
        # Retrieve & save all files uploaded by the user
        bib_file_name = None
        yml_file_name = None
        image_files_list = list()
        ## Save markdown file
        md_file_name = f"{form.name.data}article.md"
        form.md_file.data.save(f"{dir_path}/{md_file_name}")
        ## Save BibTeX file
        bibtex_file_name = f"{form.name.data}article.bib"
        form.bib_file.data.save(f"{dir_path}/{bibtex_file_name}")
        ## Save YAML file
        yaml_file_name = f"{form.name.data}article.yml"
        form.yaml_file.data.save(f"{dir_path}/{yaml_file_name}")
        # Save image files
        if form.image_files.data:
            for file in form.image_files.data:
                file.save(f"{dir_path}/{file.filename}")
                image_files_list.append(file.filename)
        ## check if biblatex is used
        biblatex_used = form.biblatex_used.data
        ## check if compound-words filter is used
        compound_used = form.compound_words_used.data

        res = create_files_dw(dir_path, md_file_name, yaml_file_name, biblatex=biblatex_used, compound=compound_used)
        if res:
            file_list = os.listdir(dir_path)
            # create a ZIP archive
            create_zip_file(dir_path, file_list)
            return render_template("maker/output.html", file_list=file_list, dir_path=dir_path)
        else:
            critical_error_logger("Create Files: Error creating files.")
            return render_template("500.html")
    else:
        return render_template("maker/dw.html", form=form)
    
## DOWNLOAD ROUTE    
@maker.route('/download/<path:dir_path>/<path:filename>')
@login_required
def download_file(dir_path, filename):
    working_directory = os.getcwd()
    return send_from_directory(working_directory, dir_path + "/" + filename, as_attachment=True)