import sys
import os
import time
import re
import json
import subprocess
import urllib3

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import requests
from tomlkit import parse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select

import inputs.locators as locators
from utils.bvt_status import update_status
from utils.endpoints import run_oc_command
from utils.logger import logger
from utils.check_cr_content import get_initialization_values

class P8BPMRest :
    def __init__(self) :
        """
        Method name: __init__
        Author: Anisha Suresh
        Description: Initializes the WebDriver with specified options and settings.
        Parameters:
            None
        Returns:
            None
        """
        logger.info("Initialising chrome driver for P8BPMREST endpoint testing.")
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
        self.namespace = self.config['configurations']['project_name']
        self.cluster = self.config['configurations']['cluster']
        self.deployment_type = self.config['configurations']['deployment_type']
        self.screenshot_path = self.config['paths']['screenshot_path']

    def get_cpd_route(self) :
        """
        Method name: get_cpd_route
        Author: Anisha Suresh
        Description: Retrieves the cpd/zen route from the deployment.
        Parameters: None
        Returns:
            cpd_route: The fetched cpd route
        """
        cpd_route = None
        try:
            cpd_route = run_oc_command(["oc get route cpd  -o jsonpath=\'{.spec.host}\'"]).strip()
            logger.info(f"The cpd route is: {cpd_route}")
        except Exception as e:
            logger.exception(f"An exception occured while fetching the zen route : {e}")
        return cpd_route
    
    def get_p8bpmrest_conn_point(self, dep_type) :
        """
        Method name: get_p8bpmrest_conn_point
        Author: Anisha Suresh
        Description: Retrieves the CPE object store workflow PE connection point from the initialization values of the CR.
        Parameters:
            dep_type : Type of deployment : (production, starter, pre-upgrde, post-upgrde)
        Returns:
            oc_cpe_obj_store_workflow_pe_conn_point_name : CPE OS workflow pe connection point name from CR
        Raises:
            None
        """
        logger.info("Getting CPE object store workflow PE connection point ... ")
        oc_cpe_obj_store_workflow_pe_conn_point_name = get_initialization_values('oc_cpe_obj_store_workflow_pe_conn_point_name', dep_type)
        if not oc_cpe_obj_store_workflow_pe_conn_point_name:
            logger.info("CPE connection point is not found in CR file.")
            return None
        logger.info(f"CPE connection point is : {oc_cpe_obj_store_workflow_pe_conn_point_name}")
        return oc_cpe_obj_store_workflow_pe_conn_point_name

    def login(self,oc_cpe_obj_store_workflow_pe_conn_point_name):
        """
        Method name: login
        Author: Anisha Suresh
        Description: Login to the P8BPMREST endpoint using the credentials and retries for maximum 3 times if fails
        Parameters:
            oc_cpe_obj_store_workflow_pe_conn_point_name : CPE OS workflow pe connection point name from CR
        Returns:
            None
        """
        zen_route = self.get_cpd_route()
        self.p8bpmrest_endpoint = f"https://{zen_route}/cpe/peengine/P8BPMREST/p8/bpm/v1/appspacenames?cp={oc_cpe_obj_store_workflow_pe_conn_point_name}"
        logger.info(f"P8BPMREST endpoint: {self.p8bpmrest_endpoint}")
        n = 0
        self.driver.get(self.p8bpmrest_endpoint)
        while(n<3) :
            try :
                try : 
                    logger.info("Trying to click on Enterprise LDAP option for login...")
                    self.driver.find_element(By.CLASS_NAME, locators.LocatorElements.enterpriseLDAP).click()
                    logger.info("Successfully clicked on Enterprise LDAP option for login!")
                except Exception as e:
                    logger.debug(f"An exception occured while trying to click Enterprise LDAP option : {e}")
                    logger.warning("Trying to select Enterprise LDAP option from dropdown for login...")
                    dropdown_element = self.driver.find_element(By.ID,"login_options")
                    select = Select(dropdown_element)
                    select.select_by_visible_text("Enterprise LDAP")
                    logger.info("Successfully seleted Enterprise LDAP option from dropdown for login!")
                self.driver.find_element(By.ID, locators.LocatorElements.acceUsername).send_keys(self.username)
                logger.info(f"Username field is filled with : {self.username}")
                self.driver.find_element(By.ID, locators.LocatorElements.accePassword).send_keys(self.password)
                logger.info(f"Password field is filled with :  {self.password}")
                self.driver.find_element(By.NAME, locators.LocatorElements.loginbtn).click()
                logger.info("Clicked on Login button!")
                WebDriverWait(self.driver,60).until(lambda d: d.execute_script('return document.readyState') == 'complete')
                time.sleep(2)
                break
            except Exception as e:
                logger.error(f"An exception occured during logging in to P8BPMREST endpoint : {e}.")
                logger.info("Retrying ...")
                n = n + 1
                self.driver.execute_script("window.open('','_blank');")
                self.driver.switch_to.window(self.driver.window_handles[-1])
                logger.info("Opened a fresh page.")
                logger.info("Loading URL again.")
                self.driver.get(self.p8bpmrest_endpoint)
                continue

    def verify_endpoint(self):
        """
        Method name: verify_endpoint
        Author: Anisha Suresh
        Description: Captures the endpoint screenshot after verification
        Parameters:
            None
        Returns:
            p8bpmrest_status : Status of P8BPMREST endpoint verification
        """
        try :
            logger.info(f"Getting page source from the endpoint")
            page_text = self.driver.page_source.lower()  
            if "error" in page_text:
                logger.error("P8BPMREST Endpoint Execution FAILED! Errors present in P8BPMREST endpoint.")
                p8bpmrest_status = "FAILED"
            else:
                logger.info("No ERROR found on the page.")
                p8bpmrest_status = "PASSED"
        except Exception as e: 
            p8bpmrest_status = "FAILED"
            logger.error(f"An exception occured during fetching the page source : {e}")
        logger.info(f"P8BPMREST Endpoint status: {p8bpmrest_status}")
        logger.info(f"Saving screenshot: {self.screenshot_path}/p8bpmrest.png")
        total_height = self.driver.get_window_size()['height']
        required_height = total_height//2
        self.driver.set_window_size(1500, required_height)
        self.driver.save_screenshot(f"{self.screenshot_path}/p8bpmrest.png")
        return p8bpmrest_status

    def close_browser(self):
        """
        Method name: close_browser
        Author: Anisha Suresh
        Description: Closes the browser after execution
        Parameters:
            None
        Returns:
            None
        """
        logger.info("Closing the web-driver.")
        self.driver.quit()

    def check_response(self,token=None,auth_param=None) : 
        """
        Method name: check_response
        Author: Anisha Suresh
        Description: Check the response from url and do verification
        Parameters:
            None
        Returns:
            p8bpmrest_status : Status of P8BPMREST endpoint verification
        """
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        response = requests.get(self.p8bpmrest_endpoint, headers=headers, auth=auth_param, verify=False)
        logger.info(f"Response status code is : {response.status_code}")
        logger.info(f"Response data is : {response.text}")
        logger.info(f"Response header is : {response.headers}")
        if response.status_code == 200 :
            p8bmrest_status = "PASSED"
        else :
            p8bmrest_status = "FAILED"
            logger.error(f"Couldn't connect. Response code : {response.status_code}. Response : {response.text}.")
        return p8bmrest_status
    
    def generate_zen_token(self) :
        """
        Method name: generate_zen_token
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Generate zen token using appLogin credentials
        Parameters:
            None
        Returns:
            access_token : IAM access token
        """
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        zen_token = ""
        try:
            # IAM URL
            iam_url = f"https://cp-console-{self.namespace}.apps.{self.cluster}.cp.fyre.ibm.com/idprovider/v1/auth/identitytoken"
            logger.info(f"IAM url : {iam_url}")

            # payload data definition
            data = {
                "grant_type": "password",
                "scope": "openid",
                "username": self.username,
                "password": self.password
            }
            logger.info(f"Payload data for response is : {data}")

            # Send a POST request 
            # `verify=False` ignores SSL cert errors
            logger.info("Requesting IAM token...")
            iam_response = requests.post(iam_url, data=data, verify=False) 
            logger.info(f"Response Code: {iam_response.status_code}") 

            match = re.search(r'"access_token":\s*"([^"]+)"',iam_response.text)
            if match :
                iam_token = match.group(1)
                logger.info(f"IAM token : {iam_token}")
            else :
                logger.error(f"IAM access token not found. Response : {iam_response.text}")
        except Exception as e:
            logger.error(f"An exception occured while trying to fetch the IAM access token : {e}")

        try:
            # ZEN url
            zen_url = f"https://cpd-{self.namespace}.apps.{self.cluster}.cp.fyre.ibm.com/v1/preauth/validateAuth"
            logger.info(f"Zen url : {zen_url}")
            headers = {
                "username": self.username,
                "iam-token": iam_token
            }
            logger.info("Requesting ZEN token...")
            zen_response = requests.get(zen_url,headers=headers,verify=False)
            logger.info(f"Response Code: {zen_response.status_code}") 
            data = json.loads(zen_response.text)

            # Extract the second accessToken
            zen_token = data.get("accessToken")
            if zen_token:
                logger.info(f"IAM token : {iam_token}")
            else :
                logger.info(f"Couldn't get zen token. Response : {zen_response.text}")
        except Exception as e:
            logger.error(f"An exception occured while trying to fetch the ZEN access token : {e}")
        return zen_token

    def p8bpmrest_test(self):
        """
        Method name: p8bpmrest_test
        Author: Anisha Suresh
        Description: Executes P8BPMREST BVT and updates status
        Parameters:
            None
        Returns:
            None
        """
        logger.info("==========================================Starting execution of P8BPMREST==========================================")
        pe_conn_point_name = self.get_p8bpmrest_conn_point(self.deployment_type)
        if not pe_conn_point_name:
            logger.warning("CPE connection point is not found in CR file. Exiting the test.")
            update_status("CPE_P8BPMREST","N/A")
            return
        self.login(pe_conn_point_name)
        ui_status = self.verify_endpoint()
        logger.info(f"UI status is {ui_status}")
        self.close_browser()
        token = self.generate_zen_token()
        auth_status = self.check_response(auth_param=(self.username, self.password))
        logger.info(f"Auth status is : {auth_status}")
        token_status = self.check_response(token=token)
        logger.info(f"Token status is : {token_status}")
        if {ui_status, auth_status, token_status} == {"PASSED"}:
            update_status("CPE_P8BPMREST","PASSED")
        else :
            update_status("CPE_P8BPMREST","FAILED")
        logger.info("==========================================Completed execution of P8BPMREST==========================================\n\n")

if __name__ == "__main__" :
    p8bmrest = P8BPMRest()
    p8bmrest.p8bpmrest_test()