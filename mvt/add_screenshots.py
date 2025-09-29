import sys
import os
# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import PyPDF2
from datetime import date
from termcolor import colored
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from PIL import Image
from reportlab.lib import colors
from tomlkit import parse
from utils.logger import logger

def get_mvt_images(screenshot_path):
    """
        Method name: get_mvt_images
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Retrive the captured component version images for MVT report
        Parameters:
            None
        Returns:
            None
    """
    
    logger.info("Retrieving MVT images from the screenshot folder.")
    all_files = os.listdir(screenshot_path)
    mvt_images = [os.path.join(screenshot_path, file) for file in all_files if file.startswith("mvt_")]
    return mvt_images

def add_screenshots_to_pdf(product):
    """
        Method name: add_screenshots_to_pdf
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Attach the captured component version images to MVT report
        Parameters:
            None
        Returns:
            mvt_images : list of mvt images
    """
    logger.info("Starting to add screenshots to the PDF report...")
    with open("./inputs/config.toml","r") as file :
        input_data = parse(file.read())

    run_date = date.today()
    logger.info(f"MVT run date : {run_date}")
    pdf_path = f"{input_data['paths']['generated_reports_path']}/MVT_{product}_{input_data['configurations']['project_name']}_{input_data['configurations']['deployment_type']}_{input_data['configurations']['cluster']}_{run_date}.pdf"
    logger.info("Settings descriptions for MVT images.")
    descriptions = {
        "cpe": "CPE About Page",
        "nav_about": "Navigator About Page",
        "graphql_ping_page": "Graphql Ping Page",
        "tm": "Task Manager Version",
        "cmis" : "CMIS About Page"
    }
    if os.path.exists(pdf_path):
        images_path = get_mvt_images(input_data['paths']['screenshot_path'])
        if not images_path:
                logger.warning("No MVT images found. Skipping PDF update.")
                return
        # Sort the images_path list based on the order of keys in the descriptions dictionary
        sorted_images_path = sorted(images_path, key=lambda x: list(descriptions.keys()).index(x.split("mvt_")[1].split(".")[0]))
        # Create a new PDF writer
        logger.info("Creating PDF writer.")
        pdf_writer = PyPDF2.PdfWriter()
        # Open existing PDF document and add its pages to the pdf writer instance
        logger.info("Adding pages to PDF writer.")
        with open(pdf_path, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            num_pages = len(pdf_reader.pages)
            print(f"Existing PDF contains {num_pages} pages.")
            for page_num in range(num_pages):
                pdf_writer.add_page(pdf_reader.pages[page_num])
        # Create a canvas object to draw images and text
        logger.info("Creating canvas.")
        c = canvas.Canvas('temp.pdf', pagesize=letter)
        # Add heading "MVT Screenshots" only on the first page
        c.setFont("Helvetica-Bold", 16)
        c.setFillColor(colors.black)
        c.drawString(80, letter[1] - 50, "MVT Screenshots")
        # Add images and text to the canvas
        current_y = letter[1] - 100  # Start position from the top of the page, below the heading with reduced space
        for image_path in sorted_images_path:
            # Extract text after "mvt_" from the image filename
            image_name = os.path.basename(image_path)
            text = image_name.split("mvt_")[1].split(".")[0]  # Extract text after "mvt_" and before file extension
            # Get the description from the dictionary
            description = descriptions.get(text, "Unknown")
            # Styling for the text
            c.setFont("Helvetica-Bold", 12)
            c.setFillColor(colors.black)  
            # Check if the image fits on the current page along with the text
            img = Image.open(image_path)
            img_width, img_height = img.size
            aspect_ratio = img_width / img_height
            max_image_width = letter[0] * 0.8
            max_image_height = max_image_width / aspect_ratio
            if current_y - 20 - max_image_height < 50:  # Check if it fits on the current page
                c.showPage()
                current_y = letter[1] - 50  # Reset current_y for the new page
            # Draw the description and image on the canvas
            c.drawString(80, current_y, description)
            c.drawImage(image_path, x=80, y=current_y - max_image_height - 20, width=max_image_width, height=max_image_height, preserveAspectRatio=True)
            logger.info(f"Added image {image_path} with description '{description}'.")
            # Update current_y for the next image
            current_y = current_y - max_image_height - 40  # Add some space between images and descriptions
        # Save the canvas to a PDF file
        logger.info("Saving canvas.")
        c.save()
        logger.info("Temporary PDF with screenshots created.")
        # Append the temporary PDF with images to the existing PDF
        with open('temp.pdf', 'rb') as temp_file:
            temp_reader = PyPDF2.PdfReader(temp_file)
            num_temp_pages = len(temp_reader.pages)
            for page_num in range(num_temp_pages):
                pdf_writer.add_page(temp_reader.pages[page_num])
        # Save the updated PDF document
        with open(pdf_path, 'wb') as output_file:
            pdf_writer.write(output_file)
        logger.info(f"Updated PDF saved to {pdf_path}.")
        os.remove('temp.pdf')
        logger.info("Temporary file removed.")
    else:
        logger.error(f"Report file does not exist. Path : {pdf_file}")

if __name__ == "__main__":
    add_screenshots_to_pdf()
