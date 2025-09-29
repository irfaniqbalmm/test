import os
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from PIL import Image
from io import BytesIO
import time
from tomlkit import parse
from utils.logger import logger

def combine_screenshots(ss_path, filename, num_images, output_filename):
    """
    Method name: combine_screenshots
    Author: Anisha Suresh (anisha-suresh@ibm.com)
    Description: Combine the captured screenshots to make a single one.
    Parameters:
        ss_path : Path to file where all screenshots are saved
        filename : Name of the screenshot files
        num_images : number of images captured
        output_filename : Name of the output file
    Returns:
        None
    """
    logger.info(f"Combining {num_images} screenshots into a single image.")
    # Open the first image to get the dimensions
    first_image = Image.open(f'{ss_path}/{filename}0.png')
    image_width, image_height = first_image.size
    total_height = image_height * num_images
    combined_image = Image.new('RGB', (image_width, total_height))
    current_height = 0
    for i in range(num_images):
        image_path = f'{ss_path}/{filename}{i}.png'
        logger.info(f"Processing image: {image_path}")
        if os.path.exists(image_path):
            img = Image.open(image_path)
            combined_image.paste(img, (0, current_height))
            current_height += image_height
        else:
            logger.info(f"Image {image_path} not found, skipping.")
    combined_image.save(f'{ss_path}/{output_filename}.png')
    logger.info(f"Images successfully combined.")

def capture_ocp_ss(driver, id, filename, config_file_path=None):
    """
    Method name: capture_ocp_ss
    Description: Capture the screenshots one by one
    Parameters:
        driver : wed-driver currently used
        id : id of the webelement 
        filename : filename of the output image
    Returns:
        None
    """
    logger.info(f"Starting screenshot capture of {filename}")
    # Getting config file path
    if config_file_path is None or config_file_path == "":
        config_file_path = "./inputs/config.toml"

    # Parsing config file
    with open(config_file_path,"r") as file:
        config = parse(file.read())
    ss_path = config['paths']['screenshot_path']
    logger.info(f"Screenshot path is: {ss_path}")
    logger.info("Waiting for the presence of scrollable div")
    scrollable_div = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, id)))
    ignore_div1_length = 0
    ignore_div2_length = 0
    try :
        logger.info("Waiting for the presence of pane body [1]")
        ignore_div1 = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//div[@class="co-m-pane__body"][1]')))
        ignore_div1_length = ignore_div1.size['height']
    except:
        pass
    try :
        logger.info("Waiting for the presence of pane body [3]")
        ignore_div2 = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//div[@class="co-m-pane__body"][3]')))
        ignore_div2_length = ignore_div2.size['height']
    except:
        pass
    div_location = scrollable_div.location
    div_width = scrollable_div.size['width']
    div_height = scrollable_div.size['height']
    total_height = driver.execute_script("return arguments[0].scrollHeight", scrollable_div) 
    total_height = total_height - ignore_div2_length
    screenshots = []
    scroll_position = 0 + ignore_div1_length
    n=0
    logger.info("Scrolling and capturing the screenshots")
    while scroll_position < total_height:
        driver.execute_script("arguments[0].scrollTop = arguments[1];", scrollable_div, scroll_position)
        time.sleep(0.5)
        screenshot = driver.get_screenshot_as_png()
        image = Image.open(BytesIO(screenshot))
        left = div_location['x']
        top = div_location['y']
        right = left + div_width
        bottom = image.height
        # Crop the image to the specified area
        cropped_image = image.crop((left, top, right, bottom))
        cropped_image.save(f'{ss_path}/{filename}{n}.png')
        #print(f"Saved cropped image: {cropped_image_path}")
        scroll_position += div_height 
        n+=1
        screenshots.append(cropped_image)
    combine_screenshots(ss_path, filename, n, filename)
    logger.info("Screenshot capture and combination complete.")