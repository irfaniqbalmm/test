import sys
import os
# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import inputs.locators as locators
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import json
from utils.bvt_status import update_status
from tomlkit import parse
from utils.logger import logger

class BaiAutomation:
    bai_status = "FAILED"

    def __init__(self):
        """
        Method name: __init__
        Description: Initializes the WebDriver with specified options and settings.
        Parameters:
            None
        Returns:
            None
        """
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument("--incognito")
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.maximize_window()
        self.driver.implicitly_wait(10)

        with open("./inputs/config.toml", "r") as file :
            self.config = parse(file.read())
        
        self.username = self.config['credentials']['app_login_username']
        self.password = self.config['credentials']['app_login_password']
        self.deployment_type = self.config['configurations']['deployment_type']
        self.screenshot_path = self.config['paths']['screenshot_path']
        self.build = self.config['configurations']['build']

    def navigate_to_dashboard(self):
        """
        Method name: navigate_to_dashboard
        Description: Navigate to content dashboard in BAI
        Parameters:
            None
        Returns:
            None
        """
        time.sleep(3)
        logger.info("Navigating to content dashbaord...")
        i=0
        for i in (0,3) :
            try : 
                logger.info(f"Attempt {i+1}: Trying to locate the content dashboard link...")
                content_dashboard_link = self.driver.find_element(By.XPATH, locators.LocatorElements.content_db_link)
                logger.info("Content dashboard link located. Attempting to click...")
                content_dashboard_link.click()
                logger.info("Successfully navigated to the content dashboard.")
                return True
            except Exception as e:
                logger.warning(f"Attempt {i+1} failed. Exception encountered: {e}")
                logger.info("Retrying to locate and click the content dashboard link...")
                i = i + 1
                continue
        logger.error("Failed to navigate to the content dashboard after 3 attempts.")
        return False

    def login(self):
        """
        Method name: login
        Description: Login to content dashboard in BAI
        Parameters:
            None
        Returns:
            None
        """
        logger.info("==========================================Starting execution of BAI==========================================")
        # Load the endpoints.json file
        logger.info("Loading endpoints.json file...")
        with open('./inputs/endpoints.json', 'r') as json_file:
            endpoints = json.load(json_file)
        bai_desktop_route = endpoints.get("bai_desktop_route")
        logger.info(f"BAI desktop route retrieved: {bai_desktop_route}")
        logger.info("Visiting bai desktop link...")
        self.driver.get(bai_desktop_route)
        try:
            logger.info("Attempting to select Enterprise LDAP element")
            self.driver.find_element(By.CLASS_NAME, locators.LocatorElements.enterpriseLDAP).click()
        except Exception as e:
            logger.warning(f"Failed to select Enterprise LDAP element.")
            logger.warning("Attempting to select Enterprise LDAP from dropdown...")
            dropdown_element = self.driver.find_element(By.ID,"login_options")
            select = Select(dropdown_element)
            select.select_by_visible_text("Enterprise LDAP")
        logger.info(f"Entering username and password : {self.username} / {self.password}")
        self.driver.find_element(By.ID, locators.LocatorElements.acceUsername).send_keys(self.username)
        self.driver.find_element(By.ID, locators.LocatorElements.accePassword).send_keys(self.password)
        logger.info("Clicking login button...")
        self.driver.find_element(By.NAME, locators.LocatorElements.loginbtn).click()
        n=0
        while(n<2) :
            try :
                logger.info("Waiting for frame to be available and switching to it...")
                WebDriverWait(self.driver ,60).until(EC.frame_to_be_available_and_switch_to_it(0))
                logger.info("Switched to frame")
                clicked = self.navigate_to_dashboard()
                if clicked :
                    logger.info("Successfully navigated to the dashboard.")
                    break
                else :
                    raise Exception("Failed to find content dashboard")
            except Exception as e: 
                logger.error(f"Exception during login attempt {n + 1}: {e}")
                if self.deployment_type == 'starter' :
                    logger.info("Attempting another approach since deployment type is 'starter'. Switching back to default content...")
                    self.driver.switch_to.default_content()
                    logger.info("Switched back")
                    logger.info("Locating BAI dropdown...")
                    WebDriverWait(self.driver,30).until(EC.presence_of_element_located((By.XPATH,locators.LocatorElements.bai_drop)))
                    logger.info("Clicking BAI dropdown...")
                    WebDriverWait(self.driver,30).until(EC.element_to_be_clickable((By.XPATH,locators.LocatorElements.bai_drop))).click()
                    logger.info("Selecting BPC...")
                    WebDriverWait(self.driver,30).until(EC.element_to_be_clickable((By.XPATH,locators.LocatorElements.bpc))).click()
                    logger.info("Waiting for frame to be available and switching to it again...")
                    WebDriverWait(self.driver ,60).until(EC.frame_to_be_available_and_switch_to_it(0))
                    logger.info("Successfully switched to frame.")
                    clicked = self.navigate_to_dashboard()
                    if clicked :
                        logger.info("Successfully navigated to the dashboard after retry.")
                        break
                else : 
                    logger.info("Retrying login by opening a new tab...")
                    n = n+1
                    self.driver.execute_script("window.open('','_blank');")
                    self.driver.switch_to.window(self.driver.window_handles[-1])
                    self.driver.get(bai_desktop_route)
                    logger.info(f"Retrying with new tab. Attempt {n + 1}.")
                    continue  

    def take_screenshot(self):
        """
        Method name: take_screenshot
        Description: Capture screenshot of dashboard
        Parameters:
            None
        Returns:
            bai_status : status of BAI dashboard
        """
        bai_status = "FAILED"
        try :
            logger.info("Starting the screenshot capture process...")
            try : 
                logger.info("Checking for matching images of No data available error...")
                matching_images = self.driver.find_element(By.XPATH, f'//img[@src="{locators.LocatorElements.bai_src_to_check}"]')
                if matching_images :
                    logger.warning("Matching images found to NO DATA AVAILABLE error. Marking BAI status as FAILED.")
                    bai_status = "FAILED"
            except Exception as e: 
                logger.info(f"No 'ERROR' matching images found. Proceeding with other checks.")
                try:
                    logger.info("Checking for key elements in the dashboard...")
                    element_document = WebDriverWait(self.driver, 60).until(EC.visibility_of_element_located((By.XPATH, locators.LocatorElements.bai_xpath_locator1)))
                    element_total_documents = WebDriverWait(self.driver, 60).until(EC.visibility_of_element_located((By.XPATH, locators.LocatorElements.bai_xpath_locator2)))
                    element_timestamp = WebDriverWait(self.driver, 60).until(EC.visibility_of_element_located((By.XPATH, locators.LocatorElements.bai_xpath_locator3)))
                    element_classdescription = WebDriverWait(self.driver, 60).until(EC.visibility_of_element_located((By.XPATH, locators.LocatorElements.bai_xpath_locator4)))
                    element_lastmodifier = WebDriverWait(self.driver, 60).until(EC.visibility_of_element_located((By.XPATH, locators.LocatorElements.bai_xpath_locator5)))
                    element_translate = WebDriverWait(self.driver, 60).until(EC.visibility_of_element_located((By.XPATH, locators.LocatorElements.bai_xpath_locator6)))
                    elements = [element_document, element_total_documents, element_timestamp, element_classdescription, element_lastmodifier, element_translate]
                    if all(elements) :
                        bai_status = "PASSED"
                        logger.info(f"BAI status is : {bai_status}")
                except Exception as e :
                    logger.error(f"Error while checking elements: {e}")
                    bai_body_content = self.driver.find_element(By.TAG_NAME,'body').text
                    # Check if the word 'No data available yet' is present in the body content
                    if 'No data available yet' in bai_body_content:
                        bai_status = "FAILED - No data available"
                    elif 'You are not allowed to see this data' in bai_body_content:
                        bai_status = "No access to data"
                    logger.error("bai status is :" , bai_status)
            self.driver.save_screenshot(f'{self.screenshot_path}/bai.png')
        except Exception as e :
            logger.error(f"An exception occured during taking screenshots : {e}")
            bai_status = "FAILED"
        update_status("BAI_Content_Dashboard", bai_status)
        logger.info(f"BAI Content Dashboard status updated to: {bai_status}")
        return bai_status
    
    def nav_dashboard(self) :
        """
        Method name: nav_dashboard
        Description: Navigate to navigator dashboard in BAI and capture its screenshot
        Parameters:
            None
        Returns:
            nav_status : status of navigator dashboard
        """
        if "21.0.3" in self.build or "23.0.2" in self.build or "22.0.2" in self.build:
            nav_status = "N/A"
            logger.warning(f"Build : {self.build} doesn't support Navigator Dashboard. Updating sttaus to N/A value")
            update_status("BAI_Navigator_Dashboard",nav_status)
            logger.info("Navigator status updated to N/A")
            return
        self.driver.back()
        time.sleep(3)
        nav_status = "FAILED"
        try :
            WebDriverWait(self.driver ,60).until(EC.frame_to_be_available_and_switch_to_it(0))
            logger.info("switched to frame")
        except :
            logger.warning("Not able to switch to frame")
        for i in (0,3) :
            try : 
                logger.info(f"Attempt {i+1}: Trying to locate the Navigator dashboard link...")
                nav_dashboard_link = WebDriverWait(self.driver,30).until(EC.visibility_of_element_located((By.XPATH, locators.LocatorElements.nav_dashboard)))
                logger.info("Clicking on navigator dashboard link ..")
                nav_dashboard_link.click()
                logger.info("Clicked on nav dashboard link")
                try:
                    logger.info("Checking for key elements")
                    element_action = WebDriverWait(self.driver, 60).until(EC.visibility_of_element_located((By.XPATH, locators.LocatorElements.nav_xpath_locator1)))
                    element_feature = WebDriverWait(self.driver, 60).until(EC.visibility_of_element_located((By.XPATH, locators.LocatorElements.nav_xpath_locator2)))
                    element_type = WebDriverWait(self.driver, 60).until(EC.visibility_of_element_located((By.XPATH, locators.LocatorElements.nav_xpath_locator3)))
                    element_user = WebDriverWait(self.driver, 60).until(EC.visibility_of_element_located((By.XPATH, locators.LocatorElements.nav_xpath_locator4)))
                    element_featurespan = WebDriverWait(self.driver, 60).until(EC.visibility_of_element_located((By.XPATH, locators.LocatorElements.nav_xpath_locator5)))
                    element_actionspan = WebDriverWait(self.driver, 60).until(EC.visibility_of_element_located((By.XPATH, locators.LocatorElements.nav_xpath_locator6)))
                    elements = [element_action, element_feature, element_type, element_user, element_featurespan, element_actionspan]
                    if all(elements) :
                        nav_status = "PASSED"
                except :
                    pass
                self.driver.save_screenshot(f'{self.screenshot_path}/Navigator_dashboard.png')
                try :
                    body_content = self.driver.find_element(By.TAG_NAME,'body').text
                    # Check if the word 'No data available yet' is present in the body content
                    if 'No data available yet' in body_content:
                        nav_status = "FAILED - No data available"
                        logger.error("No data available error occured in nav dashbaord")
                    elif 'You are not allowed to see this data' in body_content:
                        nav_status = "No access to data"
                        logger.error("No access to data error occured in nav dashboard")
                    else :
                        nav_status = "PASSED"
                        logger.info("BVT suceeded for nav dashbaprd.")
                except Exception as e: 
                    logger.error("Couldn't fetch content from Navigator Dashboard.")
                    logger.error(f"An exception occured during fetching contents from nav dashboard : {e}")
                break
            except Exception as e: 
                self.driver.back()
                time.sleep(3)
                logger.error(f"Attempt {i+1} failed. Exception encountered: {e}")
                logger.info("Retrying to locate and click the navigator dashboard link...")
                i = i + 1
                continue
        logger.info(f"Navigator dashboard status : {nav_status}")
        update_status("BAI_Navigator_Dashboard",nav_status)
        return nav_status

    def close_browser(self):
        """
        Method name: close_browser
        Description: Closes the browser after execution
        Parameters:
            None
        Returns:
            None
        """
        logger.info("Closing webdriver")
        self.driver.quit()
        logger.info("==========================================Completed execution of BAI==========================================\n\n")

if __name__ == "__main__":
    bai_automation = BaiAutomation()
    try:
        bai_automation.login()
        bai_automation.take_screenshot()
        bai_automation.nav_dashboard()
    finally:
        bai_automation.close_browser()
