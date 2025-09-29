import os
import sys
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from tomlkit import parse

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from inputs import locators
from utils.logger import logger

class CreatePlugin():
    def __init__(self, config_file, product=None):
        """
        Method description: Initializes the class CreatePlugin.
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Parameters: 
            config_file: Path to config file
            product: Product for which plugin is created (default=None)
        Returns: None
        """

        with open(config_file, "r") as file :
            self.config = parse(file.read())

        section = "paths" 
        if product:
            section = product.lower()
        self.screenshot_path = self.config[section]['screenshot_path']
        self.download_directory = self.config[section]['download_path']

    def capture_plugin_ss(self, driver, plugin_name):
        """
        Method Name: capture_plugin_ss
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Method description: Navigates to a specific section in the application using a given selector and captures a screenshot.
        Args:
            driver (selenium.webdriver.remote.webdriver.WebDriver): The WebDriver instance used to control the browser.
            plugin_name (str): The name of the plugin for which the screenshot is to be captured.
        Returns:
            None
        Raises: None
        """
        logger.info("Capturing the screenshot...")
        total_height = driver.execute_script("return document.body.scrollHeight")
        total_width = driver.execute_script("return document.body.scrollWidth")
        required_height = total_height*2
        logger.info("Re-sizing the window.")
        driver.set_window_size(int(total_width), int(required_height))
        logger.info("Saving the screenshot")
        plugin_ss_name = plugin_name.replace(" ","")
        driver.save_screenshot(f'{self.screenshot_path}/{plugin_ss_name}.png')
        logger.info(f"Screenshot saved : {self.screenshot_path}/{plugin_ss_name}.png")

    def navigate_to_section(self, driver, section_selector):
        """
        Method Name: navigate_to_section
        Method description: Navigates to a specific section in the application using a given selector.
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Args:
            driver (selenium.webdriver.remote.webdriver.WebDriver): The WebDriver instance used to control the browser.
            section_selector (str): The XPath selector for the desired section to navigate to.
        Returns:
            None
        Raises:
            TimeoutException: If the specified section does not become visible within 60 seconds.
        """
        while(True):
            try:
                driver.find_element(By.XPATH, section_selector).click()
                logger.info("Navigating to Administration -- Clicked on administration option.")
                break
            except Exception as e:
                logger.error(f"An error occured while trying to click the administration option : {e}")
                logger.info("Retrying ...")
                driver.find_element(By.XPATH, locators.LocatorElements.navigator_slide_drawer_icon).click()
                logger.info("Clicked on slide drawer icon.")
        logger.info(f"Clicked on {section_selector} option.")
        
    def check_plugin_creation(self, driver, plugin_name):
        plugin_creation_status = "FAILED"
        try:
            plugin_locator = f"//td[contains(text(), '{plugin_name}')]"
            logger.info(f"Waiting for the presence of the plugin: {plugin_name}")
            WebDriverWait(driver,30).until(EC.visibility_of_element_located((By.XPATH, plugin_locator)))
            logger.info(f"Plugin: {plugin_name} already exists!")
            self.capture_plugin_ss(driver, plugin_name)
            plugin_creation_status = "PASSED"
        except:
            logger.info(f"Plugin {plugin_name} not found!")
        finally:
            return plugin_creation_status

    def create_plugin(self, driver, navigator_route, plugin_type):
        """
        Method Name: create_plugin
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Method description: Creates a plugin in the ICN.
        Args:
            driver (selenium.webdriver.remote.webdriver.WebDriver): The WebDriver instance used to control the browser.
            navigator_route (str): The route to navigate to in the browser.
            plugin_type (str): The type of plugin to create, either "IER" or "ICCSAP".
        Returns:
            None
        Raises: 
            Exception: If an error occurs during the plugin creation process.
        """
        plugin_creation_status = "FAILED"
        try:
            # Plugin name can be "IBM Enterprise Records"
            if plugin_type == "IER":
                plugin_name =  "IBM Enterprise Records"
                file_path = f"{self.download_directory}/IERApplicationPlugin.jar"
            elif plugin_type == "ICCSAP":
                plugin_name = "IBM Content Collector for SAP Applications Plug-In"
                file_path = f"{self.download_directory}/iccsapPlugin.jar"

            n=0
            logger.info(f"Navigating to administration : try {n+1}")
            while n<3 :
                try :
                    WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.XPATH, locators.LocatorElements.navigator_slide_drawer_icon))).click()
                    logger.info("Slide drawer icon clicked.")
                    break
                except Exception as e:
                    logger.error(f"An error occured while trying to click the slide drawer icon : {e}")
                    n += 1
                    logger.info("Retrying ...")
                    driver.execute_script("window.open('','_blank');")
                    logger.info("Opening new window.")
                    driver.switch_to.window(driver.window_handles[-1])
                    driver.get(navigator_route)
                    logger.info(f"Loading navigator route: {navigator_route}")
                    continue
            time.sleep(5)

            self.navigate_to_section(driver, locators.LocatorElements.plugin)
            logger.info("Waiting for New Plugin option to be visible.")
            WebDriverWait(driver, 60).until(EC.visibility_of_element_located((By.XPATH, locators.LocatorElements.new_plugin)))
            time.sleep(2)

            # Setting Plugin path
            self.navigate_to_section(driver, locators.LocatorElements.settings)
            logger.info("Waiting for path input box to be visible.")
            p_path = WebDriverWait(driver, 60).until(EC.visibility_of_element_located((By.XPATH, locators.LocatorElements.p_path)))
            time.sleep(5)
            p_path.click()
            p_path.clear()
            logger.info("Path box is visible. It is clicked and cleared.")
            p_path.send_keys("/opt/ibm")
            logger.info("Provided jar file path as '/opt/ibm' in the path box.")
            time.sleep(5)
            WebDriverWait(driver, 60).until(EC.visibility_of_element_located((By.XPATH, locators.LocatorElements.save_close_btn))).click()
            logger.info("Saving jar file path. Clicked on save and close button!")
            logger.info("Waiting for information field to appear.")
            WebDriverWait(driver, 100).until(EC.visibility_of_element_located((By.XPATH, locators.LocatorElements.info_field)))
            WebDriverWait(driver, 100).until(EC.visibility_of_element_located((By.XPATH, locators.LocatorElements.info_close_btn))).click()
            logger.info("Closing information box.")
            driver.refresh()
            logger.info("Refreshing the page to load the changes.")
            logger.info("Waiting for the presence of slide drawer icon.")
            WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.XPATH, locators.LocatorElements.navigator_slide_drawer_icon)))
            while(True):
                try:
                    driver.find_element(By.XPATH, locators.LocatorElements.navigator_Administration_option).click()
                    logger.info("Navigating to Administration -- Clicked on administration option.")
                    break
                except Exception as e:
                    logger.error(f"An error occured while trying to click the administration option : {e}")
                    logger.info("Retrying ...")
                    driver.find_element(By.XPATH, locators.LocatorElements.navigator_slide_drawer_icon).click()
                    logger.info("Clicked on slide drawer icon.")
            logger.info("Waiting for Plugin option to be visible.")
            WebDriverWait(driver, 60).until(EC.visibility_of_element_located((By.XPATH, locators.LocatorElements.plugin))).click()
            logger.info("Clicked on Plugins option.")
            logger.info("Waiting for New Plugin option to be visible and clickable.")
            WebDriverWait(driver, 60).until(EC.visibility_of_element_located((By.XPATH, locators.LocatorElements.new_plugin)))
            time.sleep(2)
            WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.new_plugin))).click()
            logger.info("Clicked on New Plugin option.")
            logger.info("Find the file input element by its xpath")
            file_input = driver.find_element(By.XPATH, locators.LocatorElements.ier_plugin_path)
            logger.info(f"JAR file path : {file_path}")
            if os.path.exists(file_path):
                logger.info("Sending the file path to the file input element")
                file_input.send_keys(file_path)
                WebDriverWait(driver,60).until(EC.element_to_be_clickable((By.XPATH,locators.LocatorElements.upload))).click()
                logger.info("Uploading the jar file as a plugin.")
            else:
                logger.error(f"File not found: {file_path}")
            logger.info("Waiting for Save and Close button to be visible.")
            time.sleep(30)
            WebDriverWait(driver, 60).until(EC.visibility_of_element_located((By.XPATH, locators.LocatorElements.save_close_btn)))
            WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.save_close_btn))).click()
            logger.info("Saving the upload -- clicked on the Save and Close button.")
            time.sleep(5)
            logger.info("Checking if plugin already exists.")
            plugin_creation_status = self.check_plugin_creation(driver, plugin_name)
            self.capture_plugin_ss(driver, plugin_name)
        except Exception as e:
            raise Exception(f"Failed to create {plugin_type} in ICN: {e}")
        finally:
            return plugin_creation_status
    