import sys
import os
# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import json
import time
from tomlkit import parse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.bvt_status import update_status
from utils.logger import logger

class ICCSAP():
    def __init__(self, is_sanity=False):
        """
        Method name: __init__
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Initializes the WebDriver with specified options and settings.
        Parameters:
            is_sanity: True if this is for sanity tests (default=False)
        Returns:
            None
        """
        logger.info("==========================================Starting execution of ICCSAP==========================================")
        self.is_sanity = is_sanity
        if is_sanity:
            config_file = "./component_sanity_tests/config/config.toml"
            section = "iccsap"
        else:
            config_file = "./inputs/config.toml"
            section = "paths"

        with open(config_file,"r") as file :
            self.config = parse(file.read())
        
        self.username = self.config['credentials']['app_login_username']
        self.password = self.config['credentials']['app_login_password']
        self.deployment_type = self.config['configurations']['deployment_type']
        self.screenshot_path = self.config[section]['screenshot_path']
        self.download_directory = self.config[section]['download_path']

        logger.info("Initializes the WebDriver for ICCSAP BVT.")
        chrome_options = webdriver.ChromeOptions()
        prefs = {
            "download.default_directory": self.download_directory,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        chrome_options.add_experimental_option("prefs", prefs)
        # chrome_options.add_argument("--incognito")
        chrome_options.add_argument('--ignore-certificate-errors')

        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.maximize_window()
        self.driver.implicitly_wait(10)
        self.iccsap_status = "FAILED"
    
    def file_exists_in_directory(self, file):
        """
        Method name: file_exists_in_directory
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Check if the files exists in the directory
        Parameters:
            file : name of file to be checked
        Returns:
            True if exists else False
        """
        files = [f for f in os.listdir(self.download_directory) if f == file]
        return len(files) > 0
    
    def navigate_to_iccsap(self):
        """
        Method name: navigate_to_iccsap
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Load iccsap page, download the jar files and captures the screenshots.
        Parameters:
            None
        Returns:
            iccsap_status : Status of iccsap verification
        """
        iccsap_status = "FAILED"
        logger.info(f"Fetching iccsap endpoint")
        with open('./inputs/endpoints.json', 'r') as json_file:
            endpoints = json.load(json_file)
        iccsap_files_route = endpoints.get("iccsap_files_route")
        logger.info(f"ICCSAP files endpoint is : {iccsap_files_route}")
        try:
            logger.info("Loading ICCSAP endpoint.")
            self.driver.get(iccsap_files_route)
            logger.info("Resizing window")
            total_height = self.driver.execute_script("return document.body.scrollHeight")
            total_width = self.driver.execute_script("return document.body.scrollWidth")
            required_height = total_height*2
            self.driver.set_window_size(int(total_width/2), int(required_height))
            self.driver.save_screenshot(f'{self.screenshot_path}/iccsap.png')
            logger.info(f"Saving screenshot : {self.screenshot_path}/iccsap.png")
            self.driver.maximize_window()
        except Exception as e:
            logger.error(f"An exception occured while trying to capture ICCSAP page : {e}")
        n=0
        while n<3 :
            logger.info(f"Checking ICCSAP for errors -> Try : {n+1}")
            try :
                body_content = self.driver.find_element(By.TAG_NAME,'body').text
                
                # Check if the word 'Error' is present in the body content
                if 'Error' in body_content:
                    logger.error(f"ERROR present in ICCSAP page : \n {body_content}")
                    self.iccsap_status = "FAILED"
                    if not self.is_sanity:
                        update_status("ICCSAP", self.iccsap_status)
                    else:
                        update_status("ui_verification", self.iccsap_status, "ICCSAP")
                    return self.iccsap_status
            except Exception as e: 
                logger.error(f"An exception occured while trying to check for errors in ICCSAP page : {e}")
            try : 
                logger.info("Waiting fo the ICCSAP heading to be present.")
                e1 = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, '/html/body/h1')))
                logger.info("Heading found.")
                break
            except Exception as e: 
                logger.error(f"An exception occured while waiting for the heading : {e}")
                logger.info("Retrying ...")
                logger.info("Opening new window.")
                self.driver.execute_script("window.open('','_blank);")
                logger.info("Switching to new window.")
                self.driver.switch_to.window(self.driver.window_handles[-1])
                self.driver.get(iccsap_files_route)
                logger.info(f"Loading the iccsap files endpoint : {iccsap_files_route}")
                logger.info("Resizing the window")
                total_height = self.driver.execute_script("return document.body.scrollHeight")
                total_width = self.driver.execute_script("return document.body.scrollWidth")
                required_height = total_height*2
                self.driver.set_window_size(int(total_width/2), int(required_height))
                if self.is_sanity:
                    self.driver.save_screenshot(f'{self.screenshot_path}/iccsap_ui.png')
                else:
                    self.driver.save_screenshot(f'{self.screenshot_path}/iccsap.png')
                logger.info(f"Saving screenshot : {self.screenshot_path}/iccsap.png")
                self.driver.maximize_window()
                logger.info("Maximised the window back.")
                n = n + 1
        try : 
            logger.info("Finding the link to ICCSAP Plugins jar file")
            plugins = self.driver.find_element(By.XPATH,"//tbody/tr[1]/td[@class='name']/a")
            plugins.click()
            logger.info("Found the link element and clicked on it.")
            logger.info("Waiting for the download of plugins jar file to be completed.")
            time.sleep(11)

            logger.info("Finding the link to ICCSAP Tasks jar file")
            tasks = self.driver.find_element(By.XPATH,"//tbody/tr[2]/td[@class='name']/a")
            tasks.click()
            logger.info("Found the link element and clicked on it.")
            logger.info("Waiting for the download of plugins jar file to be completed.")
            time.sleep(11)
            jar_files = "PASSED"
        except Exception as e:
            logger.error(f"An exception occured while downloading the jar files : {e}")
            jar_files = "FAILED"
        logger.info(f"Capturing the downloads page ...")
        logger.info("Opening a new window")
        self.driver.execute_script("window.open('', '_blank');")
        self.driver.switch_to.window(self.driver.window_handles[-1])
        logger.info("Switched to new window")
        self.driver.get('chrome://downloads/')
        logger.info("Loading the chrome downloads page.")
        time.sleep(2)
        try:
            logger.info("Waiting for the download element of iccsapPlugin.jar")
            e2 = WebDriverWait(self.driver, 30).until(lambda driver: self.file_exists_in_directory("iccsapPlugin.jar"))
            logger.info("Found iccsapPlugin.jar")
            logger.info("Waiting for the download element of iccsapTasks.jar")
            e3 = WebDriverWait(self.driver, 30).until(lambda driver: self.file_exists_in_directory("iccsapTasks.jar"))
            logger.info("Found iccsapTasks.jar")
            if e1 and e2 and e3 and jar_files:
                self.iccsap_status = "PASSED"
        except Exception as e:
            logger.error(f"An exception occured while trying to find the downloads : {e}")
            self.iccsap_status = "FAILED"
        logger.info("Resizing the window.")
        total_height = self.driver.execute_script("return document.body.scrollHeight")
        required_height = total_height*3/4
        self.driver.set_window_size(1920, int(required_height))
        self.driver.save_screenshot(f'{self.screenshot_path}/iccsap_jar_files.png')  
        logger.info(f"Saving the screenshot of downloads page : {self.screenshot_path}/iccsap_jar_files.png")
        if not self.is_sanity:
            update_status("ICCSAP", self.iccsap_status)
        else:
            update_status("ui_verification", self.iccsap_status, "ICCSAP")
        return self.iccsap_status

    def close_browser(self):
        """
        Method name: close_browser
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Closes the browser after execution
        Parameters:
            None
        Returns:
            None
        """
        logger.info("Closing the webdriver.")
        self.driver.quit()
        logger.info("==========================================Completed execution of ICCSAP==========================================\n\n")

if __name__ == "__main__":
    iccsap = ICCSAP()
    iccsap.navigate_to_iccsap()
    iccsap.close_browser()
