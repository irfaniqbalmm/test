import sys
import os
# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import json
import time
from termcolor import colored
from tomlkit import parse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import inputs.locators as locators
from utils.bvt_status import update_status
from utils.logger import logger

class CMISAutomation:
    cmis_cp4ba_status = "FAILED"

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
        # Load the endpoints.json file
        logger.info("==========================================Starting execution of CMIS==========================================")
        logger.info("Fetching cmis endpoint from endpoint.json file.")
        with open('./inputs/endpoints.json', 'r') as json_file:
            endpoints = json.load(json_file)
        self.cmis_route = endpoints.get("cmis_route")
        logger.info(f"CMIS endpoint : {self.cmis_route}")

        with open("./inputs/config.toml","r") as file :
            self.config = parse(file.read())
        
        self.username = self.config['credentials']['app_login_username']
        self.password = self.config['credentials']['app_login_password']
        self.screenshot_path = self.config['paths']['screenshot_path']
        self.deployment_type = self.config['configurations']['deployment_type']

        logger.info("Initializing Chrome driver for CMIS CP4BA BVT")
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument("--incognito")
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.maximize_window()
        self.driver.implicitly_wait(10)

    def navigate_to_cmis(self):
        """
        Method name: navigate_to_cmis
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Navigates to cmis url
        Parameters:
            None
        Returns:
            None
        """
        logger.info(f"Loading cmis cp4ba url : {self.cmis_route}")
        self.driver.get(self.cmis_route)
        try : 
            logger.info("Trying to click on Enterprise LDAP option for login")
            self.driver.find_element(By.CLASS_NAME, locators.LocatorElements.enterpriseLDAP).click()
            logger.info("Clicked on Enterprise LDAP option for login")
        except Exception as e:
            logger.info("Couldn't select Enterprise LDAP.")
            logger.info("Trying to select Enterprise LDAP option from dropdown for login")
            dropdown_element = self.driver.find_element(By.ID,"login_options")
            select = Select(dropdown_element)
            select.select_by_visible_text("Enterprise LDAP")
            logger.info("Selected Enterprise LDAP option from dropdown for login")

    def login_to_cmis(self):
        """
        Method name: login_to_cmis
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Logins to cmis url
        Parameters:
            None
        Returns:
            None
        """
        self.driver.find_element(By.ID, locators.LocatorElements.acceUsername).send_keys(self.username)
        logger.info(f"Username field filled with : {self.username}")
        self.driver.find_element(By.ID, locators.LocatorElements.accePassword).send_keys(self.password)
        logger.info(f"Password field filled with : {self.password}")
        self.driver.find_element(By.NAME, locators.LocatorElements.loginbtn).click()
        logger.info("Clicked on login button.")
        time.sleep(5)

    def take_screenshot(self, filename):
        """
        Method name: take_screenshot
        Description: Captures the screenshot by moving to end of the page
        Parameters:
            filename : filename of the screenshot
        Returns:
            None
        """
        logger.info("Scrolling to end.")
        self.driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
        self.driver.get_screenshot_as_file(filename)
        logger.info(f"Screenshot captured : {filename}.")

    def explore_cmis_service(self):
        """
        Method name: explore_cmis_service
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Expand cmis and verifies the component
        Parameters:
            None
        Returns:
            cmis_status :  Status of cmis component verification
        """
        n=0
        while n<3 :
            logger.info(f"Try {n+1} of CMIS CP4BA Bvt execution...")
            try :
                if self.deployment_type != 'starter' :
                    element1 = self._click_element_by_xpath(locators.LocatorElements.cmis_service_collection)
                    element2 = self._click_element_by_xpath(locators.LocatorElements.cmis_uri_template)
                    if element1 and element2 :
                        cmis_cp4ba_status = "PASSED"
                    else:
                        cmis_cp4ba_status = "FAILED"
                else : 
                    element1 = self._click_element_by_xpath(locators.LocatorElements.cmis_design)
                    logger.info("Expanded cmis design element")
                    element2 = self._click_element_by_xpath(locators.LocatorElements.cmis_target)
                    logger.info("Expanded cmis target element")
                    element3 = self._click_element_by_xpath(locators.LocatorElements.cmis_devos)
                    logger.info("Expanded cmis devos element")
                    element4 = self._click_element_by_xpath(locators.LocatorElements.cmis_content)
                    logger.info("Expanded cmis content element")
                    element5 = self._click_element_by_xpath(locators.LocatorElements.cmis_design_template)
                    logger.info("Expanded cmis design_template element")
                    element6 = self._click_element_by_xpath(locators.LocatorElements.cmis_target_template)
                    logger.info("Expanded cmis target template  element")
                    element7 = self._click_element_by_xpath(locators.LocatorElements.cmis_devos_template)
                    logger.info("Expanded cmis devos template  element")
                    element8 = self._click_element_by_xpath(locators.LocatorElements.cmis_content_template)
                    logger.info("Expanded cmis content template  element")
                    if element1 and element2 and element3 and element4:
                        cmis_cp4ba_status = "PASSED"
                    else:
                        cmis_cp4ba_status = "FAILED"
                break
            except Exception as e: 
                logger.error(f"An exception occured during CMIS CP4BA execution : {e}")
                n += 1
                cmis_cp4ba_status = "FAILED"
                logger.info("Retrying CMIS CP4BA BVT execution...")
                self.driver.execute_script("window.open('','_blank');")
                self.driver.switch_to.window(self.driver.window_handles[-1])
                logger.info("Switched to new window.")
                self.driver.get(self.cmis_route)
                logger.info(f"Loading cmis cp4ba route : {self.cmis_route}")
                continue
            
        time.sleep(5)
        logger.info("Reducing screen size.")
        self.driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
        self.driver.execute_script("document.body.style.zoom='80%'") 
        logger.info("Capturing screenshot.")
        self.take_screenshot(f'{self.screenshot_path}/cmis1.png')
        logger.info("Re-sizing screen.")
        self.driver.execute_script("document.body.style.zoom='100%'") 
        time.sleep(1)
        logger.info("Capturing version details for MVT.")
        self._click_element_by_xpath(locators.LocatorElements.cmis_about)
        self.driver.implicitly_wait(10)
        self.take_screenshot(f'{self.screenshot_path}/mvt_cmis.png')
        update_status("CMIS_CP4BA",cmis_cp4ba_status)
        logger.info(f"CMIS CP4BA status : {cmis_cp4ba_status}")
        return cmis_cp4ba_status

    def _click_element_by_id(self, element_id):
        """
        Method name: _click_element_by_id
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Clicks an element by its id
        Parameters:
            element_id : id of the web element
        Returns:
            None
        """
        try :
            logger.info(f"Clicking element with ID : {element_id}")
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, element_id))).click()
        except Exception as e:
            logger.error(f"An exception occured while trying to click the element : {e}")

    def _click_element_by_xpath(self, xpath):
        """
        Method name: _click_element_by_xpath
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Clicks an element by its xpath
        Parameters:
            xpath : xpath of the web element
        Returns:
            e : web element object
        """
        try :
            logger.info(f"Clicking element with xpath : {xpath}")
            element = WebDriverWait(self.driver, 60).until(EC.element_to_be_clickable((By.XPATH, xpath)))
            element.click()
            return (element)
        except Exception as e:
            logger.error(f"An exception occured while trying to click the element : {e}")
            return

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
        logger.info("Closing webdriver.")
        self.driver.close()


class CMISOCPAutomation:
    cmis_ocp_status = "FAILED"

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
        # Load the endpoints.json file
        with open('./inputs/endpoints.json', 'r') as json_file:
            endpoints = json.load(json_file)
        self.cmis_ocp_route = endpoints.get("cmis_ocp_route")

        with open("./inputs/config.toml","r") as file :
            self.config = parse(file.read())
        
        self.screenshot_path = self.config['paths']['screenshot_path']
        self.deployment_type = self.config['configurations']['deployment_type']
        
        logger.info("Initializing Chrome driver for CMIS OCP BVT")
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument("--incognito")
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.maximize_window()

    def navigate_to_cmis(self):
        """
        Method name: navigate_to_cmis
        Description: Navigates to cmis url
        Parameters:
            None
        Returns:
            None
        """
        logger.info(f"Loading cmis ocp route: {self.cmis_ocp_route}")
        self.driver.get(self.cmis_ocp_route)
        self.driver.implicitly_wait(10)

    def take_screenshot(self, filename):
        """
        Method name: take_screenshot
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Captures the screenshot by moving to end of the page
        Parameters:
            filename : filename of the screenshot
        Returns:
            None
        """
        logger.info("Scrolling to end.")
        self.driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
        self.driver.get_screenshot_as_file(filename)
        logger.info(f"Screenshot captured : {filename}.")

    def explore_cmis_service(self):
        """
        Method name: explore_cmis_service
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Expand cmis and verifies the component
        Parameters:
            None
        Returns:
            cmis_status :  Status of cmis component verification
        """
        n=0
        while n<3 :
            logger.info(f"Try {n+1} of CMIS OCP Bvt execution...")
            try :
                if self.deployment_type != 'starter' :
                    element1 = self._click_element_by_xpath(locators.LocatorElements.cmis_service_collection)
                    element2 = self._click_element_by_xpath(locators.LocatorElements.cmis_uri_template)
                    if element1 and element2 :
                        cmis_ocp_status = "PASSED"
                    else:
                        cmis_ocp_status = "FAILED"
                else : 
                    element1 = self._click_element_by_xpath(locators.LocatorElements.cmis_design)
                    logger.info("Expanded cmis design element")
                    element2 = self._click_element_by_xpath(locators.LocatorElements.cmis_target)
                    logger.info("Expanded cmis target element")
                    element3 = self._click_element_by_xpath(locators.LocatorElements.cmis_devos)
                    logger.info("Expanded cmis devos element")
                    element4 = self._click_element_by_xpath(locators.LocatorElements.cmis_content)
                    logger.info("Expanded cmis content element")
                    element5 = self._click_element_by_xpath(locators.LocatorElements.cmis_design_template)
                    logger.info("Expanded cmis design_template element")
                    element6 = self._click_element_by_xpath(locators.LocatorElements.cmis_target_template)
                    logger.info("Expanded cmis target template  element")
                    element7 = self._click_element_by_xpath(locators.LocatorElements.cmis_devos_template)
                    logger.info("Expanded cmis devos template  element")
                    element8 = self._click_element_by_xpath(locators.LocatorElements.cmis_content_template)
                    logger.info("Expanded cmis content template  element")
                    if element1 and element2 and element3 and element4:
                        cmis_ocp_status = "PASSED"
                    else:
                        cmis_ocp_status = "FAILED"
                break
            except : 
                n += 1
                cmis_ocp_status = "FAILED"
                logger.info("Retrying CMIS OCP BVT execution...")
                self.driver.execute_script("window.open('','_blank');")
                logger.info("Switched to new window.")
                self.driver.switch_to.window(self.driver.window_handles[-1])
                self.driver.get(self.cmis_ocp_route)
                logger.info(f"Loading cmis_ocp_route  : {self.cmis_ocp_route}")
                continue

        time.sleep(5)
        logger.info("Reducing screen size.")
        self.driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
        self.driver.execute_script("document.body.style.zoom='80%'") 
        logger.info("Capturing screenshot.")
        self.take_screenshot(f'{self.screenshot_path}/cmis_2.png')
        update_status("CMIS_OCP",cmis_ocp_status)
        logger.info(f"CMIS OCP status is : {cmis_ocp_status}")
        return cmis_ocp_status
        
    def _click_element_by_id(self, element_id):
        """
        Method name: _click_element_by_id
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Clicks an element by its id
        Parameters:
            element_id : id of the web element
        Returns:
            None
        """
        try :
            logger.info(f"Clicking element with ID : {element_id}")
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, element_id)))
        except Exception as e:
            logger.error(f"An exception occured while trying to click the element : {e}")

    def _click_element_by_xpath(self, xpath):
        """
        Method name: _click_element_by_xpath
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Clicks an element by its xpath
        Parameters:
            xpath : xpath of the web element
        Returns:
            e : web element object
        """
        try :
            logger.info(f"Clicking element with xpath : {xpath}")
            element = WebDriverWait(self.driver, 60).until(EC.element_to_be_clickable((By.XPATH, xpath)))
            element.click()
            return (element)
        except Exception as e:
            logger.error(f"An exception occured while trying to click the element : {e}")
            return

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
        logger.info("Closing webdriver.")
        self.driver.close()
        logger.info("==========================================Completed execution of CMIS==========================================\n\n")

if __name__ == "__main__" :
    cmis_automation = CMISAutomation()
    cmis_automation.navigate_to_cmis()
    cmis_automation.login_to_cmis()
    cmis_automation.explore_cmis_service()
    cmis_automation.close_browser()

    cmis_ocp_automation = CMISOCPAutomation()
    cmis_ocp_automation.navigate_to_cmis()
    cmis_ocp_automation.explore_cmis_service()
    cmis_ocp_automation.close_browser()
    