import sys
import os
# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import json
import time
import pyautogui
from tomlkit import parse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import inputs.locators as locators
from utils.bvt_status import update_status
from utils.logger import logger

class TaskManagerPage:

    def __init__(self):
        """
        Method name: __init__
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Initializes the WebDriver with specified options and settings.
        Parameters:
            None
        Returns:
            None
        """
        logger.info("==========================================Starting execution of TM==========================================")
        with open("./inputs/config.toml","r") as file :
            self.config = parse(file.read())
        
        self.username = self.config['credentials']['app_login_username']
        self.password = self.config['credentials']['app_login_password']
        self.screenshot_path = self.config['paths']['screenshot_path']

        logger.info("Initializing chrome web-driver for TM bvt")
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--incognito")
        chrome_options.add_argument('--ignore-certificate-errors')
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.maximize_window()
        self.driver.implicitly_wait(10)

        self.tm_status = "FAILED"
        with open('./inputs/endpoints.json','r') as json_file :
            endpoints = json.load(json_file)
        self.taskmanager_route = endpoints.get("taskmanager_route")

    def navigate_to_task_manager(self):
        """
        Method name: navigate_to_task_manager
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Login to taskmanager page
        Parameters:
            None
        Returns:
            None
        """
        self.driver.get(self.taskmanager_route)
        logger.info(f"Loading TM endpoint : {self.taskmanager_route}")
        try : 
            self.driver.find_element(By.CLASS_NAME, locators.LocatorElements.enterpriseLDAP).click()
        except :
            dropdown_element = self.driver.find_element(By.ID,"login_options")
            select = Select(dropdown_element)
            select.select_by_visible_text("Enterprise LDAP")
            logger.info("Clicked on Enterprise LDAP option.")
        username_input = WebDriverWait(self.driver, 60).until(EC.element_to_be_clickable((By.ID, locators.LocatorElements.acceUsername)))
        username_input.send_keys(self.username)
        logger.info(f"Send username as : {self.username}")
        password_input = WebDriverWait(self.driver,60).until(EC.element_to_be_clickable((By.ID, locators.LocatorElements.accePassword)))
        logger.info(f"Send password as : {self.password}")
        password_input.send_keys(self.password)
        login_button = WebDriverWait(self.driver,60).until(EC.element_to_be_clickable((By.NAME, locators.LocatorElements.loginbtn)))
        login_button.click()
        logger.info("Clicked login button.")

    def take_screenshot(self):
        """
        Method name: take_screenshot
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Capture the screenshot of TM and version details for mvt
        Parameters:
            None
        Returns:
            tm_status : Status of the taskmanager - PASSED or FAILED
        """
        n=0
        while n<3 :
            logger.info(f"TM bvt try : {n+1}")
            try :
                logger.info("Waiting for TM verfication element to be clickable.")
                element = WebDriverWait(self.driver, 60).until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.tm_verify)))
                if element:
                    logger.info("TM verification element found.")
                    self.tm_status = "PASSED"
                break
            except Exception as e:
                logger.error(f"An exception occured during TM bvt execution : {e}")
                logger.info("Retrying ...")
                n+=1
                self.tm_status = "FAILED"
                logger.info("Loading a new window.")
                self.driver.execute_script("window.open('','_blank');")
                logger.info("Switching to the new window.")
                self.driver.switch_to.window(self.driver.window_handles[-1])
                logger.info(f"Loading the tm endpoint again in new window.")
                self.driver.get(self.taskmanager_route)
                continue
        time.sleep(2)
        self.driver.get_screenshot_as_file(f'{self.screenshot_path}/taskmanager.png')
        logger.info(f"Screenshot saved : {self.screenshot_path}/taskmanager.png")
        try:
            logger.info("Capturing the version screenshot for MVT ...")
            logger.info("Waiting for the presence ECM configuration element.")
            version = WebDriverWait(self.driver,60).until(EC.presence_of_element_located((By.XPATH,locators.LocatorElements.tm_ecm)))
            logger.info("ECM element located, scrolling into view")
            self.driver.execute_script("arguments[0].scrollIntoView(true);", version)
            # Crop the screenshot to the portion containing the element
            mvt_screenshot_path = f'{self.screenshot_path}/mvt_tm.png'
            logger.info(f"Saving screenshot : {self.screenshot_path}/mvt_tm.png")
            self.driver.save_screenshot(mvt_screenshot_path)
            logger.info("Resizing screenshot captured.")
            top_left_x = 0
            top_left_y = 0
            width = pyautogui.size()[0]  # Width of the screen
            height = pyautogui.size()[1] // 4  # One-fourth of the screen height
            try:
                img = pyautogui.screenshot(region=(top_left_x, top_left_y, width, height))
                img.save(mvt_screenshot_path)
            except Exception as e:
                logger.error(f"An exception occured while trying to resize the image : {e}")
        except Exception as e:
            logger.error(f"An error occured while capturing version details.")
            logger.warning("For versions 25.0.0 or above, the version details are not included in the TM UI due to security reasons.")
            logger.exception(f"An exception occured while capturing version details of TM: {e}")
        update_status("TM",self.tm_status)
        return self.tm_status
    
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
        logger.info("Closing the web-driver.")
        self.driver.quit()
        logger.info("==========================================Completed execution of TM==========================================\n\n")

if __name__ == "__main__":
    task_manager_page = TaskManagerPage()
    task_manager_page.navigate_to_task_manager()
    task_manager_page.take_screenshot()
    task_manager_page.close_browser()


