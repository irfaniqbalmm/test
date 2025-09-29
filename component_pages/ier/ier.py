import sys
import os
# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
import json
import time
import pyautogui
from termcolor import colored
from tomlkit import parse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from utils.bvt_status import update_status
from utils.logger import logger

class IERDownloader:
    ier_status = "FAILED"

    def __init__(self, is_sanity=False):
        """
        Method name: __init__
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Initializes the WebDriver with specified options and settings.
        Parameters:
            None
        Returns:
            None
        """
        logger.info("==========================================Starting execution of IER==========================================")
        
        self.is_sanity = is_sanity
        if is_sanity:
            config_file = "./component_sanity_tests/config/config.toml"
            section = "ier"
        else:
            config_file = "./inputs/config.toml"
            section = "paths"
        
        with open(config_file,"r") as file :
            self.config = parse(file.read())
            
        self.screenshot_path = self.config[section]['screenshot_path']
        self.download_directory = self.config[section]['download_path']

        logger.info("Initializing the WebDriver for IER BVT.")
        chrome_options = webdriver.ChromeOptions()
        prefs = {
            "download.default_directory": self.download_directory,
            "safebrowsing.enabled": True
        }  
        chrome_options.add_experimental_option("prefs", prefs)
        chrome_options.add_argument('--ignore-certificate-errors')
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.maximize_window()

    def setup_driver(self):
        """
        Method name: setup_driver
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Setup the webdriver to download the IER file and checks if the downloaded file is present in the specified location.
        Parameters:
            None
        Returns:
            ier_status : Status of the IER download process (PASSED or FAILED)
        """
        logger.info("Fetching IER endpoint.")
        with open('./inputs/endpoints.json','r') as json_file :
            endpoints = json.load(json_file)
        ier_route = endpoints.get("ier_route")
        self.driver.get(ier_route)
        logger.info(f"Loading IER route : {ier_route}")
        self.driver.implicitly_wait(10)
        time.sleep(10)
        n = 0
        while(n<3) :
            logger.info(f"IER BVT try : {n+1}.")
            try :
                body_content = self.driver.find_element(By.TAG_NAME,'body').text
                logger.info(f"IER page content : {body_content}")
                # Check if the word 'Error' is present in the body content
                if 'Error' in body_content:
                    logger.error(f"Error found in IER page : {body_content}")
                    ier_status = "FAILED"
                    update_status("IER",ier_status)
                    return ier_status 
            except Exception as e: 
                logger.info(f"An exception occured while fetching IER page : {e}")
                pass
        
            try : 
                logger.info("Checking if the IER file is downloaded ...")
                element1 = WebDriverWait(self.driver, 60).until(
                    lambda driver: self.file_exists_in_directory()
                )
                if element1 :
                    logger.info("IER jar file downloaded successfully.")
                    ier_status = "PASSED"
                    break
                else : 
                    logger.error("IER jar file download failed.")
                    ier_status = "FAILED"
            except Exception as e:
                logger.error(f"An exception occured file while trying to check the IER file download : {e}.")
                n += 1
                ier_status = "FAILED"
                logger.info("Retrying ...")
                self.driver.execute_script("window.open('','_blank');")
                logger.info("Loading new window.")
                self.driver.switch_to.window(self.driver.window_handles[-1])
                logger.info("Switching to the new window.")
                self.driver.get(ier_route)
                logger.info(f"Loading IER endpoint : {ier_route}")
                continue
        update_status("IER",ier_status)
        return ier_status
    
    def file_exists_in_directory(self):
        """
        Method name: file_exists_in_directory
        Description: Checks if the IER file exists in the specified download directory.
            None
        Returns:
            True if file present else False.
        """
        files = [f for f in os.listdir(self.download_directory) if f == "IERApplicationPlugin.jar"]
        return len(files) > 0

    def capture_top_screen(self):
        """
        Method name: capture_top_screen
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Captures the top of the screen of ier using pyautogui library.
        Parameters:
            None
        Returns:
            screenshot_path : Path of the saved screenshot
        """
        logger.info("Capturing IER pgae screenshot ...")
        top_left_x = 0
        top_left_y = 0
        width = pyautogui.size()[0]  # Width of the screen
        height = pyautogui.size()[1] // 4  # One-fourth of the screen height
        screenshot_path = f'{self.screenshot_path}//ier1.png'
        logger.info(f"Screenshot path : {screenshot_path}")
        try:
            img = pyautogui.screenshot(region=(top_left_x, top_left_y, width, height))
            img.save(screenshot_path)
            logger.info("Saving screenshot.")
            return screenshot_path
        except Exception as e:
            logger.error(f"An exception occured during capturing IER screenshot : {e}")
            return None

    def capture_downloads_screen(self):
        """
        Method name: capture_downloads_screen
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Captures the download screen of chrome browser to get the latest downloads.
        Parameters:
            None
        Returns:
            screenshot_path : Path of the saved screenshot
        """
        logger.info("Capturing the download screen of chrome browser to get the latest downloads.")
        self.driver.execute_script("window.open('', '_blank');")
        self.driver.switch_to.window(self.driver.window_handles[-1])
        logger.info("Loaded and switched to new window.")
        self.driver.get('chrome://downloads/')
        logger.info("Loading the chrome downloads page.")
        time.sleep(2)
        screenshot_path = f'{self.screenshot_path}//ier2.png'
        logger.info(f"Downloads screenshot path : {screenshot_path}")
        try:
            total_height = self.driver.execute_script("return document.body.scrollHeight")
            required_height = total_height/2
            self.driver.set_window_size(1920, int(required_height))
            logger.info("Resizing window")
            self.driver.save_screenshot(screenshot_path)
            logger.info("Screenshot saved.")
            return screenshot_path
        except Exception as e:
            return None

    def close_driver(self):
        """
        Method name: close_driver
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Closes the browser after execution
        Parameters:
            None
        Returns:
            None
        """
        logger.info("Closing the chrome web driver.")
        self.driver.quit()
        logger.info("==========================================Completed execution of IER==========================================\n\n")

if __name__ == "__main__":
    ier_downloader = IERDownloader()
    ier_downloader.setup_driver()
    top_screen_path = ier_downloader.capture_top_screen()
    downloads_screen_path = ier_downloader.capture_downloads_screen()
    ier_downloader.close_driver()
