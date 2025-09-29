import sys
import os
# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from BAI_BVT.bai_utils.bai_report import generate_bai_html_report
from reports.generate_report import generate_html_report
import pdfkit
from datetime import datetime
import pikepdf
import shutil
from tomlkit import parse
from utils.logger import logger

def compress_pdf(pdf_file_path):
    """
    Method name: compress_pdf
    Description : Compress the generated PDF using pikepdf.
    Parameters: 
        pdf_file_path - (str) path to thte generated PDF file
    Returns:
        None
    """
    try:
        logger.info("Compressing the pdf ...")
        # Open the generated PDF
        logger.info("Opening the current pdf file...")
        with pikepdf.open(pdf_file_path,allow_overwriting_input=True) as pdf:
            # Save the PDF with compression 
            logger.info("Saving as a compressed pdf.")
            pdf.save(pdf_file_path, compress_streams=True)
        logger.info(f"PDF compressed successfully : {pdf_file_path}")
    except Exception as e:
        logger.error(f"An exception occured during PDF compression: {e}")

def convert_html_to_pdf(config_file=None):
    """
    Method name: convert_html_to_pdf
    Description: Convert the generated html report to pdf format
    Parameters:
        None
    Returns:
        None
    """
    logger.info("==========================================Starting convertion the generated html report to pdf format==========================================")
    options = {
        'margin-top': '0mm',
        'margin-right': '0mm',
        'margin-bottom': '0mm',
        'margin-left': '0mm',
        'enable-local-file-access': '',
        'disable-smart-shrinking': '',
        'no-pdf-compression': '',
        'viewport-size': '1024x768',  # Ensures the viewport for rendering
    }
    if config_file is not None and config_file != "":
        #Creating report
        generate_bai_html_report()
        report_name = 'BVT_BAI'
    else:
        config_file = "./inputs/config.toml"

        #Creating report
        generate_html_report()
        report_name = 'BVT_CP4BA'

    with open(config_file,"r") as file :
        config = parse(file.read())
    
    d = datetime.now().date()

    html_file_path = config['paths']['report_path']
    if config['configurations']['user'] != "admin" :
        pdf_file_path = f"{config['paths']['generated_reports_path']}/{report_name}_{config['configurations']['project_name']}_{config['configurations']['deployment_type']}_{config['configurations']['cluster']}_non_admin_{d}.pdf"
    else : 
        pdf_file_path = f"{config['paths']['generated_reports_path']}/{report_name}_{config['configurations']['project_name']}_{config['configurations']['deployment_type']}_{config['configurations']['cluster']}_{d}.pdf"
    html_file = os.path.abspath(html_file_path)
    pdf_file = os.path.abspath(pdf_file_path)
    path_wkthmltopdf = shutil.which('wkhtmltopdf')
    config = pdfkit.configuration(wkhtmltopdf=path_wkthmltopdf)
    try :
        logger.info("Converting html to pdf ... ")
        logger.info(f"PDF file path : {pdf_file}")
        pdfkit.from_file(html_file, pdf_file, options=options, configuration=config)
        logger.info("Converted to pdf file.")
        compress_pdf(pdf_file)
    except Exception as e:
        print(e)
    logger.info("==========================================Completed convertion the generated html report to pdf format==========================================\n\n")
    

if __name__ == "__main__" :
    convert_html_to_pdf()
