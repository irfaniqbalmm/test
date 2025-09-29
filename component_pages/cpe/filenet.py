import sys
import os
import json
import time

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from tomlkit import parse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import inputs.locators as locators
from component_pages.ldap_login import LdapLogin
from utils.bvt_status import update_status
from utils.logger import logger

class Filenet :
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
        logger.info("==========================================Starting execution of CPE Filenet Endpoints==========================================")
        logger.info("Initialising chrome driver for CPE Filenet tests")
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument("--incognito")
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.maximize_window()
        self.driver.implicitly_wait(10)

        with open("./inputs/config.toml","r") as file :
            self.config = parse(file.read())
        self.username = self.config['credentials']['app_login_username']
        self.password = self.config['credentials']['app_login_password']
        self.screenshot_path = self.config['paths']['screenshot_path']

        # Load the endpoints.json file
        with open('./inputs/endpoints.json', 'r') as json_file:
            endpoints = json.load(json_file)
        self.filenet_process_services_ping_page =  endpoints.get("FileNet_Process_Services_ping_page")
        self.filenet_process_services_details_page = endpoints.get("FileNet_Process_Services_details_page")
        self.filenet_p8_content_engine_web_service_page = endpoints.get("FileNet_P8_Content_Engine_Web_Service_page")
        self.filenet_process_engine_web_service_page = endpoints.get("FileNet_Process_Engine_Web_Service_page")
        self.content_search_services_health_check = endpoints.get("Content_Search_Services_health_check")

    def test_cpe_filenet_page(self, page_name, page_url, screenshot_name, status_key, locator=None):
        """
        Method name: test_cpe_filenet_page
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Captures the screenshot of Content Search Services health check page after verification if locator is given
        Parameters:
            page_name (str) : Name of the page being verified.
            page_url (str) : Url of the page being verified.
            screenshot_name (str) : Name to save the screenshot of the page.
            status_key (str) : Status key from bvt_status.py to be recorded in the report.
            locator : Locator to be verified. Defaults to None.
        Returns:
            page_status : Status of page verification
        """
        logger.info(f"Loading {page_name} : {page_url}")
        self.driver.get(page_url)
        page_status = "FAILED"
        n=0
        login_succeeded = False
        while(n<2) :
            logger.info(f"Attempt : #{n+1}")
            try : 
                logger.info(f"Trying to verify the {page_name}")
                WebDriverWait(self.driver, 30).until(lambda d: d.execute_script('return document.readyState') == 'complete')
                if locator:
                    WebDriverWait(self.driver,30).until(EC.presence_of_element_located((By.XPATH,locator)))
                page_status = "PASSED"
                break
            except Exception as e: 
                logger.error(f"An exception occured during {page_name} BVT : {e}")
                n = n+1
                if not login_succeeded:
                    try : 
                        ldap_login = LdapLogin()
                        login_succeeded = ldap_login.login(self.driver, self.content_search_services_health_check, self.username, self.password)
                        logger.info("Trying to login to the page ...")
                    except Exception as e :
                        logger.error(f"An exception occured while trying to login to {page_name}: {e}")
                        n = n+1
                        page_status = "FAILED"
                        logger.info("Retrying...")
                        logger.info("Loading a new blank page")
                        self.driver.execute_script("window.open('','_blank');")
                        logger.info("Switching to the new window.")
                        self.driver.switch_to.window(self.driver.window_handles[-1])
                        self.driver.get(page_url)
                        continue
        time.sleep(2)
        logger.info(f"Saving screenshot : {self.screenshot_path}/{screenshot_name}.png")
        self.driver.save_screenshot(f'{self.screenshot_path}/{screenshot_name}.png')
        update_status(status_key, page_status)
        return page_status

    def fps_ping_page(self):
        """
        Method name: fps_ping_page
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Calls the FPS Ping Page test
        Parameters:
            None
        Returns:
            fps_ping_page_status : Status of FPS ping page verification
        """
        fps_ping_page_status = self.test_cpe_filenet_page("FPS Ping page", self.filenet_process_services_ping_page,
                                                          "fps_ping_page", "FileNet_Process_Services_ping_page",
                                                          locator=locators.LocatorElements.fps_ping_page)
        return fps_ping_page_status
    
    def fps_details_page(self):
        """
        Method name: fps_details_page
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Calls the FPS details Page test
        Parameters:
            None
        Returns:
            fps_details_page : Status of FPS details page verification
        """
        self.driver.execute_script("window.open('','_blank');")
        self.driver.switch_to.window(self.driver.window_handles[-1])
        fps_details_page_status = self.test_cpe_filenet_page("FPS details page", self.filenet_process_services_details_page, 
                                                             "fps_details_page", "FileNet_Process_Services_details_page",
                                                             locator=locators.LocatorElements.fps_details_page)
        return fps_details_page_status
    
    def pe_web_services(self) :
        """
        Method name: pe_web_services
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Calls the FileNet Process Engine Web Service page test
        Parameters:
            None
        Returns:
            pe_web_services_page_status : Status of FileNet Process Engine Web Service page verification
        """
        self.driver.execute_script("window.open('','_blank');")
        self.driver.switch_to.window(self.driver.window_handles[-1])
        pe_web_services_page_status = self.test_cpe_filenet_page("CE web services page", self.filenet_process_engine_web_service_page, 
                                                                 "pe_web_page", "FileNet_Process_Engine_Web_Service_page")
        return pe_web_services_page_status
    
    def ce_web_services(self) :
        """
        Method name: ce_web_services
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Calls the FileNet P8 Content Engine Web Service page test
        Parameters:
            None
        Returns:
            ce_web_services_page_status : Status of FileNet P8 Content Engine Web Service page verification
        """
        self.driver.execute_script("window.open('','_blank');")
        self.driver.switch_to.window(self.driver.window_handles[-1])
        ce_web_services_page_status = self.test_cpe_filenet_page("CE web services page", self.filenet_p8_content_engine_web_service_page, 
                                                                 "ce_web_page", "FileNet_P8_Content_Engine_Web_Service_page")
        return ce_web_services_page_status
    
    def css_health_check(self) :
        """
        Method name: css_health_check
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Calls the Content Search Services health check page test
        Parameters:
            None
        Returns:
            pe_web_services_page_status : Status of Content Search Services health check page verification
        """
        logger.info("CSS Health Check Page BVT")
        self.driver.execute_script("window.open('','_blank');")
        self.driver.switch_to.window(self.driver.window_handles[-1])
        self.driver.get(self.content_search_services_health_check)
        css_health_status = self.test_cpe_filenet_page("CSS Health Check page", self.content_search_services_health_check, 
                                                        "css_web_page", "Content_Search_Services_health_check",
                                                        locator=locators.LocatorElements.css_check)
        return css_health_status
    
    def close_filenet(self) :
        """
        Method name: close_filenet
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Closes the browser after execution
        Parameters:
            None
        Returns:
            None
        """
        logger.info("Clossing the web-driver.")
        self.driver.quit()
        logger.info("==========================================Completed execution of CPE Filenet Endpoints==========================================\n\n")
    
if __name__ == "__main__" :
    fn = Filenet()
    fps_ping_page_status = fn.fps_ping_page()
    fps_details_page_status = fn.fps_details_page()
    pe_web_services_page_status = fn.pe_web_services()
    ce_web_services_page_status = fn.ce_web_services()
    css_health_status = fn.css_health_check()
    fn.close_filenet()

    