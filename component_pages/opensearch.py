import sys
import os
# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import json
import time
import subprocess
from termcolor import colored
from tomlkit import parse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.bvt_status import update_status
from utils.logger import logger

class Opensearch :

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
        logger.info("==========================================Starting execution of Opensearch==========================================")
        with open("./inputs/config.toml","r") as file :
            self.config = parse(file.read())
        self.screenshot_path = self.config['paths']['screenshot_path']

        logger.info("Initializing webdriver for opensearch BVT")
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument("--incognito")
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.maximize_window()
        self.driver.implicitly_wait(10)

    def get_tls_issuer(self) :
        """
        Method name: get_tls_issuer
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Checks if opensearch is using cp4ba-tls-issuer
        Parameters:
            None
        Returns:
            True/False
        """
        try :
            logger.info("Checking the tls-issuer in opensearch.")
            try:
                tls_issuer = subprocess.check_output(["oc", "get", "ElasticsearchCluster", "opensearch", "-o", "jsonpath={.spec.tlsIssuer}"], universal_newlines=True)
            except Exception as e:
                logger.warning(f"An exception occured while getting ElasticsearchCluster: {e}. Retrying with 'Cluster' type.")
                tls_issuer = subprocess.check_output(["oc", "get", "Cluster", "opensearch", "-o", "jsonpath={.spec.tlsIssuer}"], universal_newlines=True)
            if str(tls_issuer) == "cp4ba-tls-issuer" :
                logger.info("The tls-issuer is 'cp4ba-tls-issuer'.")
                return True
            else :
                logger.info("The tls-issuer is NOT 'cp4ba-tls-issuer'.")
                return False
        except Exception as e :
            logger.error(f"An exception occured while checking the tls-issuer : {e}")

    def contains_error(self,logs):
        """
        Method name: contains_error
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Checks if error is present in passed string
        Parameters:
            logs : Value in which error has to be checked
        Returns:
            True/False
        Raises: None
        """
        return '[ERROR]' in logs

    def check_logs(self):
        """
        Method name: check_logs
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Download and checks if error is present in logs
        Parameters:
            None
        Returns:
            True/False
        Raises :
            CalledProcessError
        """
        try :
            logger.info("Getting the opensearch logs")
            get_log_command = ["oc", "logs", "opensearch-ib-6fb9-es-server-all-0", "-c", "elasticsearch"]
            logger.info(f"Executing the command : {get_log_command}")
            logs = subprocess.check_output(get_log_command, stderr=subprocess.STDOUT, text=True)
            if self.contains_error(logs) :
                logger.info("Opensearch logs contain errors.")
                return True
        except subprocess.CalledProcessError as e:
            logger.error(f"An exception occured while fetching the logs : {e}")
            return f"Error fetching logs: {e.output}"
        
    def login_load(self):
        """
        Method name: login_load
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Login to opensearch and load the opensearch page
        Parameters:
            None
        Returns:
            opensearch_status : Status of opensearch execution
        """
        logger.info("Login to opensearch and load the opensearch page")
        with open('./inputs/endpoints.json','r') as json_file :
            endpoints = json.load(json_file)
        opensearch_url = endpoints.get("opensearch_url")
        self.driver.get(opensearch_url)
        logger.info(f"Loading opensearch url : {opensearch_url}")
        opensearch_status = "FAILED"
        n=0
        while(n<2) :
            logger.info(f"Opensearch BVT try : {n+1}")
            try : 
                logger.info("Waiting for the 'json-formatter' element")
                WebDriverWait(self.driver,30).until(EC.presence_of_element_located((By.XPATH,'//div[@class=\'json-formatter-container\']')))
                logger.info("Element found! Opensearch/elasticsearch UI loaded without any errors.")
                opensearch_status = "PASSED"
                break
            except Exception as e: 
                logger.error(f"An exception occured during loading the Opensearch page : {e}")
                logger.info("Retrying ...")
                n = n+1
                opensearch_status = "FAILED"
                logger.info("Loading new window.")
                self.driver.execute_script("window.open('','_blank');")
                logger.info("Switching to new window.")
                self.driver.switch_to.window(self.driver.window_handles[-1])
                logger.info(f"Loading the url in new window.")
                self.driver.get(opensearch_url)
                continue
        time.sleep(2)
        logger.info("Resizing the page.")
        total_height = self.driver.execute_script("return document.body.scrollHeight")
        required_height = total_height*2
        self.driver.set_window_size(1920, int(required_height))
        self.driver.save_screenshot(f'{self.screenshot_path}/opensearch.png')
        logger.info(f"Savings screenshot : {self.screenshot_path}/opensearch.png.")
        logger.info("Checking if opensearch is using external certificate...")
        ext_tls_issuer = self.get_tls_issuer()
        if ext_tls_issuer :
            logger.info("Opensearch/elasticsearch is using external certificate")
            if self.check_logs() :
                opensearch_status = "FAILED"
            opensearch_status += " - External Certificate Used"
        else : 
            logger.info("External Certificate Not Used")
        update_status("Opensearch",opensearch_status)
        return opensearch_status
    
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
        self.driver.close()
        logger.info("==========================================Completed execution of Opensearch==========================================\n\n")
    
if __name__ == "__main__" :
    opensearch = Opensearch()
    opensearch_status = opensearch.login_load()
    opensearch.close_browser()
    