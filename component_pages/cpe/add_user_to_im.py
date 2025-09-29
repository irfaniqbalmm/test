import sys
import os
# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
import subprocess
import base64
from tomlkit import parse
import inputs.locators as locators
from utils.logger import logger
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class AddUserIM:
    def __init__(self) -> None:
        """
        Method name: __init__
        Description: Initializes the WebDriver with specified options and settings.
        Parameters:
            None
        Returns:
            None
        """
        chrome_options =  webdriver.ChromeOptions()
        chrome_options.add_argument("--incognito")
        chrome_options.add_argument('--ignore-certificate-errors')
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.maximize_window()
        self.driver.implicitly_wait(10)
        logger.info("Initialised chrome driver for Adding user to IM Page")

        with open("./inputs/config.toml","r") as file :
            config = parse(file.read())
            
        self.project_name = config['configurations']['project_name']
        self.cluster = config['configurations']['cluster']
        self.username = config['credentials']['app_login_username']

    def get_platform_idp_cred(self,project_name) :
        """
        Method name: get_platform_idp_cred
        Description: Get the cpadmin login credentials from the platform-auth-idp-credentials secret and decode them form base64 format.
        Parameters:
            None
        Returns:
            username : admin username
            pwd : admin password
        """
        logger.info("Getting platform-idp credentials ...")
        pwd_command = [
            'oc', 'get', 'secret', 'platform-auth-idp-credentials',
            '-n', project_name,
            '-o', 'jsonpath="{.data[\'admin_password\']}"'
        ]
        uname_command = [
            'oc', 'get', 'secret', 'platform-auth-idp-credentials',
            '-n', project_name,
            '-o', 'jsonpath="{.data[\'admin_username\']}"'
        ]
        # Run the 'oc get' command to get the encoded password
        logger.info("Running command to fetch admin password...")
        pwd_process = subprocess.Popen(pwd_command, stdout=subprocess.PIPE)
        encoded_pwd, _ = pwd_process.communicate()
        encoded_pwd = encoded_pwd.decode('utf-8').strip()
        # Use base64 module to decode the password
        pwd = base64.b64decode(encoded_pwd).decode('utf-8').strip()

        logger.info("Running command to fetch admin username...")
        # Run the 'oc get' command to get the encoded username
        uname_process = subprocess.Popen(uname_command, stdout=subprocess.PIPE)
        encoded_uname, _ = uname_process.communicate()
        encoded_uname = encoded_uname.decode('utf-8').strip()
        # Use base64 module to decode the username
        uname = base64.b64decode(encoded_uname).decode('utf-8').strip()
        logger.info(f"IDP Admin username retrived : {uname}")
        logger.info(f"IDP Admin password retrived : {pwd}")
        logger.info("Successfully retrieved platform-idp credentials!")
        return uname,pwd

    def login_to_im(self):
        """
        Method name: login_to_im
        Description: Login to the IM page using the credentials provided in the input.py file and retries for maximum 3 times if fails
        Parameters:
            None
        Returns:
            None
        """
        logger.info("==========================================Starting to add user and roles to IM==========================================")
        logger.info("Adding user to IM ... ")
        username,password = self.get_platform_idp_cred(self.project_name)
        cpd_route = f"https://cpd-{self.project_name}.apps.{self.cluster}.cp.fyre.ibm.com/zen/#/homepage"
        logger.info(f"Accessing CPD (zen) route {cpd_route}")
        self.driver.get(cpd_route)
        n=0
        while(n<3) :
            try :
                logger.info(f"Logging into IM. Try #{n+1}")
                self.driver.find_element(By.ID, locators.LocatorElements.acceUsername).send_keys(username)
                self.driver.find_element(By.ID, locators.LocatorElements.accePassword).send_keys(password)
                self.driver.find_element(By.NAME, locators.LocatorElements.loginbtn).click()
                WebDriverWait(self.driver,60).until(lambda d: d.execute_script('return document.readyState') == 'complete')
                break
            except Exception as e:
                logger.error(f"An exception occured during login : {e}")
                n = n + 1
                self.driver.execute_script("window.open('','_blank');")
                self.driver.switch_to.window(self.driver.window_handles[-1])
                self.driver.get(cpd_route)
                continue
        if n<3 :
            logger.info("Login to IM successful")
        else :
            logger.error("Couldn't login to IM.")
            logger.critical("Exiting non-admin BVT!!")
            exit()
    
    def add_user(self) :
        """
        Method name: add_user
        Description: Add non-admin user to the IM page 
        Parameters:
            None
        Returns:
            None
        """
        logger.info("Adding user to IM ...")
        try : 
            WebDriverWait(self.driver,30).until(EC.visibility_of_element_located((By.XPATH,locators.LocatorElements.manage_users)))
            WebDriverWait(self.driver,30).until(EC.element_to_be_clickable((By.XPATH,locators.LocatorElements.manage_users))).click()
            WebDriverWait(self.driver,40).until(EC.visibility_of_element_located((By.XPATH,locators.LocatorElements.add_users)))
            WebDriverWait(self.driver,40).until(EC.element_to_be_clickable((By.XPATH,locators.LocatorElements.add_users))).click()
            user_field =  WebDriverWait(self.driver,30).until(EC.presence_of_element_located((By.XPATH,locators.LocatorElements.search_user)))
            WebDriverWait(self.driver,30).until(EC.visibility_of_element_located((By.XPATH,locators.LocatorElements.search_user))).click()
            user_field.send_keys(self.username)
            WebDriverWait(self.driver,60).until(EC.visibility_of_element_located((By.XPATH,locators.LocatorElements.non_admin_user)))
            WebDriverWait(self.driver,30).until(EC.element_to_be_clickable((By.XPATH,locators.LocatorElements.non_admin_user))).click()
            WebDriverWait(self.driver,30).until(EC.visibility_of_element_located((By.XPATH,locators.LocatorElements.next_button)))
            WebDriverWait(self.driver,30).until(EC.element_to_be_clickable((By.XPATH,locators.LocatorElements.next_button))).click()
            logger.info("User selected.")
            WebDriverWait(self.driver,30).until(EC.visibility_of_element_located((By.XPATH,locators.LocatorElements.assign_roles)))
            WebDriverWait(self.driver,30).until(EC.visibility_of_element_located((By.XPATH,locators.LocatorElements.next_button)))
            WebDriverWait(self.driver,30).until(EC.element_to_be_clickable((By.XPATH,locators.LocatorElements.next_button))).click()
            WebDriverWait(self.driver,30).until(EC.visibility_of_element_located((By.XPATH,locators.LocatorElements.automation_dev_role)))
            WebDriverWait(self.driver,30).until(EC.element_to_be_clickable((By.XPATH,locators.LocatorElements.automation_dev_role))).click()
            logger.info("Added automation developer role to user.")
            WebDriverWait(self.driver,30).until(EC.visibility_of_element_located((By.XPATH,locators.LocatorElements.user_role)))
            WebDriverWait(self.driver,30).until(EC.element_to_be_clickable((By.XPATH,locators.LocatorElements.user_role))).click()
            logger.info("Added user role to user.")
            WebDriverWait(self.driver,30).until(EC.visibility_of_element_located((By.XPATH,locators.LocatorElements.next_button)))
            WebDriverWait(self.driver,30).until(EC.element_to_be_clickable((By.XPATH,locators.LocatorElements.next_button))).click()
            WebDriverWait(self.driver,30).until(EC.visibility_of_element_located((By.XPATH,locators.LocatorElements.limited)))
            WebDriverWait(self.driver,30).until(EC.visibility_of_element_located((By.XPATH,locators.LocatorElements.user_add_button)))
            WebDriverWait(self.driver,30).until(EC.element_to_be_clickable((By.XPATH,locators.LocatorElements.user_add_button))).click()
            WebDriverWait(self.driver,40).until(EC.visibility_of_element_located((By.XPATH,locators.LocatorElements.testa1ecmuser01_link)))
            logger.info("Successfully added user to IM")
        except Exception as e :
            logger.error(f"Couldn't add user to IM. An exception occured while adding user to IM : {e}")
    
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
        logger.info("==========================================Finished adding user and roles to IM==========================================")
        self.driver.close()

if __name__ == "__main__" :
    adduser = AddUserIM()
    adduser.login_to_im()
    adduser.add_user()
    adduser.close_browser()
    