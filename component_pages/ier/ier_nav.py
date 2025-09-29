import sys
import os
# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
import json
import time
import traceback 
from termcolor import colored
from tomlkit import parse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException
import inputs.locators as locators
from utils.bvt_status import update_status
from utils.logger import logger

class IER_NavigatorAutomation : 
    ier_plugin_status = "FAILED"
    
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
        logger.info("==========================================Starting execution of IER Plugin==========================================")
        logger.info("Initialising the WebDriver for IER Plugin BVT tests.")
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--incognito")
        chrome_options.add_argument('--ignore-certificate-errors')

        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.maximize_window()
        self.driver.implicitly_wait(2)

        with open("./inputs/config.toml","r") as file :
            self.config = parse(file.read())
            
        self.username = self.config['credentials']['app_login_username']
        self.password = self.config['credentials']['app_login_password']
        self.screenshot_path = self.config['paths']['screenshot_path']
        self.download_directory = self.config['paths']['download_path']

        with open('./inputs/endpoints.json', 'r') as json_file:
            endpoints = json.load(json_file)
        self.navigator_route = endpoints.get("navigator_route")

    def file_exists_in_directory(self):
        """
        Method name: file_exists_in_directory
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Checks if the IER file exists in the specified download directory.
            None
        Returns:
            True if file present else False.
        """
        files = [f for f in os.listdir(self.download_directory) if f == "IERApplicationPlugin.jar"]
        return len(files) > 0

    def login_to_navigator(self):
        """
        Method name: login_to_navigator
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Login to the navigator page
        Parameters:
            None
        Returns:
            None
        """
        logger.info("Uploading IER plugin to navigator.")
        try :
            logger.info("Trying to find the jar file downloaded from IER bvt.")
            WebDriverWait(self.driver, 60).until(lambda driver : self.file_exists_in_directory())
        except TimeoutException:
            logger.error(f"Timeout exception occured while trying to find the jar file : {TimeoutException}")
            self.ier_plugin_status = "FAILED"
            return 0
        logger.info("JAR file found!")
        try:
            logger.info(f"Loading navigator url : {self.navigator_route}")
            self.driver.get(self.navigator_route)
            # Logging in
            try : 
                self.driver.find_element(By.CLASS_NAME, locators.LocatorElements.enterpriseLDAP).click()
            except :
                dropdown_element = self.driver.find_element(By.ID,"login_options")
                select = Select(dropdown_element)
                select.select_by_visible_text("Enterprise LDAP")
            logger.info("Clicked on Enterprise LDAP option.")
            self.driver.find_element(By.ID, locators.LocatorElements.acceUsername).send_keys(self.username)
            logger.info(f"Send username as : {self.username}")
            self.driver.find_element(By.ID, locators.LocatorElements.accePassword).send_keys(self.password)
            logger.info(f"Send password as : {self.password}")
            self.driver.find_element(By.NAME, locators.LocatorElements.loginbtn).click()
            logger.info("Clicked login button.")
            time.sleep(5)
        except Exception as e:
            logger.error(f"An error occurred during login: {e}")
            traceback.print_exc()  # Print detailed stack trace
        return 1
    
    def navigate_to_administration(self):
        """
        Method name: navigate_to_administration
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Navigates to administration & IER installs the plugin in navigator using the download ier jar file.
        Parameters:
            None
        Returns:
            ier_plugin_status : Status of IER pluign install
        """
        n=0
        logger.info(f"Navigating to administration : try {n+1}")
        while n<3 :
            try :
                WebDriverWait(self.driver, 60).until(EC.presence_of_element_located((By.XPATH, locators.LocatorElements.navigator_slide_drawer_icon))).click()
                logger.info("Slide drawer icon clicked.")
                break
            except Exception as e:
                logger.error(f"An error occured while trying to click the slide drawer icon : {e}")
                n += 1
                logger.info("Retrying ...")
                self.driver.execute_script("window.open('','_blank');")
                logger.info("Opening new window.")
                self.driver.switch_to.window(self.driver.window_handles[-1])
                self.driver.get(self.navigator_route)
                logger.info(f"Loading navigator route: {self.navigator_route}")
                continue
        time.sleep(5)
        while(True):
            try:
                self.driver.find_element(By.XPATH, locators.LocatorElements.navigator_Administration_option).click()
                logger.info("Clicked on navigator administration option!")
                break
            except Exception as e:
                logger.error(f"An error occured while trying to click the administration option : {e}")
                logger.info("Retrying ...")
                self.driver.find_element(By.XPATH, locators.LocatorElements.navigator_slide_drawer_icon).click()
                logger.info("Slide drawer icon clicked.")
        logger.info("Waiting for Connections to be visible.")
        WebDriverWait(self.driver, 60).until(EC.visibility_of_element_located((By.XPATH, locators.LocatorElements.connections)))
        logger.info("Connections is visible now.")
        WebDriverWait(self.driver, 60).until(EC.visibility_of_element_located((By.XPATH, locators.LocatorElements.settings))).click()
        logger.info("Clicked on Settings option.")
        logger.info("Waiting for path input box to be visible.")
        p_path = WebDriverWait(self.driver, 60).until(EC.visibility_of_element_located((By.XPATH, locators.LocatorElements.p_path)))
        time.sleep(5)
        p_path.click()
        p_path.clear()
        logger.info("Path box is visible. It is clicked and cleared.")
        p_path.send_keys("/opt/ibm")
        logger.info("Provided jar file path as '/opt/ibm' in the path box.")
        time.sleep(5)
        WebDriverWait(self.driver, 60).until(EC.visibility_of_element_located((By.XPATH, locators.LocatorElements.save_close_btn))).click()
        logger.info("Saving jar file path. Clicked on save and close button!")
        logger.info("Waiting for information field to appear.")
        WebDriverWait(self.driver, 100).until(EC.visibility_of_element_located((By.XPATH, locators.LocatorElements.info_field)))
        WebDriverWait(self.driver, 100).until(EC.visibility_of_element_located((By.XPATH, locators.LocatorElements.info_close_btn))).click()
        logger.info("Closing information box.")
        self.driver.refresh()
        logger.info("Refreshing the page to load the changes.")
        logger.info("Waiting for the presence of slide drawer icon.")
        WebDriverWait(self.driver, 60).until(EC.presence_of_element_located((By.XPATH, locators.LocatorElements.navigator_slide_drawer_icon)))
        while(True):
            try:
                self.driver.find_element(By.XPATH, locators.LocatorElements.navigator_Administration_option).click()
                logger.info("Navigating to Administration -- Clicked on administration option.")
                break
            except Exception as e:
                logger.error(f"An error occured while trying to click the administration option : {e}")
                logger.info("Retrying ...")
                self.driver.find_element(By.XPATH, locators.LocatorElements.navigator_slide_drawer_icon).click()
                logger.info("Clicked on slide drawer icon.")
        logger.info("Waiting for Plugin option to be visible.")
        WebDriverWait(self.driver, 60).until(EC.visibility_of_element_located((By.XPATH, locators.LocatorElements.plugin))).click()
        logger.info("Clicked on Plugins option.")
        logger.info("Waiting for New Plugin option to be visible and clickable.")
        WebDriverWait(self.driver, 60).until(EC.visibility_of_element_located((By.XPATH, locators.LocatorElements.new_plugin)))
        time.sleep(2)
        WebDriverWait(self.driver, 60).until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.new_plugin))).click()
        logger.info("Clicked on New Plugin option.")
        logger.info("Find the file input element by its xpath")
        file_input = self.driver.find_element(By.XPATH, locators.LocatorElements.ier_plugin_path)
        file_path = f"{self.download_directory}/IERApplicationPlugin.jar"
        logger.info(f"JAR file path : {file_path}")
        if os.path.exists(file_path):
            logger.info("Sending the file path to the file input element")
            file_input.send_keys(file_path)
            WebDriverWait(self.driver,60).until(EC.element_to_be_clickable((By.XPATH,locators.LocatorElements.upload))).click()
            logger.info("Uploading the jar file as a plugin.")
        else:
            logger.error(f"File not found: {file_path}")
        logger.info("Waiting for Save and Close button to be visible.")
        time.sleep(30)
        WebDriverWait(self.driver, 60).until(EC.visibility_of_element_located((By.XPATH, locators.LocatorElements.save_close_btn)))
        WebDriverWait(self.driver, 60).until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.save_close_btn))).click()
        logger.info("Saving the upload -- clicked on the Save and Close button.")
        time.sleep(5)
        ier_plugin_status = "FAILED"
        try :
            logger.info("Performing IER Plugin Upload check.")
            logger.info("Waiting for the IER Enterprise Plugin to be visible in Plugins")
            WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.XPATH, locators.LocatorElements.ier_check)))
            ier_plugin_status = "PASSED"
        except Exception as e:
            logger.error(f"An exception as occured while waiitng for the IER Plugin : {e}")
            ier_plugin_status = "FAILED"
        update_status("IER_Plugin",ier_plugin_status)
        logger.info("Capturing the screenshot...")
        total_height = self.driver.execute_script("return document.body.scrollHeight")
        total_width = self.driver.execute_script("return document.body.scrollWidth")
        required_height = total_height*0.75
        logger.info("Re-sizing the window.")
        self.driver.set_window_size(int(total_width), int(required_height))
        logger.info("Saving the screenshot")
        self.driver.save_screenshot(f'{self.screenshot_path}/IER_Plugin.png')
        logger.info(f"Screenshot saved : {self.screenshot_path}/IER_Plugin.png")
        return ier_plugin_status
    
    def close_navigator(self):
        """
        Method name: close_navigator
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Closes the browser after execution
        Parameters:
            None
        Returns:
            None
        """
        logger.info("Closing web-driver.")
        self.driver.quit()
        logger.info("==========================================Completed execution of IER Plugin==========================================\n\n")

if __name__ == "__main__":
    nav = IER_NavigatorAutomation()
    e = nav.login_to_navigator()
    if e == 1 :
        nav.navigate_to_administration()
        nav.close_navigator()
    else :
        pass
    