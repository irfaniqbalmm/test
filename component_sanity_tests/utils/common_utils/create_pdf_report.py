import os
import shutil
import sys

from tomlkit import parse
import pdfkit
import pikepdf

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from component_sanity_tests.exceptions.ier_exception import IERSanityTestException
from component_sanity_tests.exceptions.iccsap_exception import ICCSAPSanityTestException
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

def convert_html_to_pdf(product, config_file):
    """
    Method name: convert_html_to_pdf
    Description: Convert the generated html report to pdf format
    Parameters:
        None
    Returns:
        None
    """
    product = product.lower()
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

    with open(config_file, "r") as file :
        config = parse(file.read())
    
    html_file_path = config[product]['report_path']
    pdf_file_path = f"{config[product]['generated_reports_path']}/{product}_sanity_tests_report.pdf"
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
        logger.exception(f"An exception occured while tryint o convert the html report to PDF: {e}")
        if product == "IER":
            raise IERSanityTestException("Failed to convert html report to PDF", cause=e) from e
        elif product == "ICCSAP":
            raise ICCSAPSanityTestException("Failed to convert html report to PDF", cause=e) from e
        
    logger.info("==========================================Completed convertion the generated html report to pdf format==========================================\n\n")
    

if __name__ == "__main__" :
    convert_html_to_pdf()
