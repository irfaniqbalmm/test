import time
import base64
import re
import configparser
import subprocess

from tomlkit import parse
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By

import utils.login as login
import inputs.locators as locators
from utils.logger import logger
from component_pages.navigator.nav_cmod import NavigatorCMOD
from component_pages.cpe.cpe import CpeAdmin

cred_cache = None

class MultildapBVTConfigs:
    def __init__(self):
        """
        Method name: __init__
        Description: Initializes the WebDriver with specified options and settings and fetching namespace,cluster from config.ini file
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
        self.wait = WebDriverWait(self.driver, 60)

        config = configparser.ConfigParser()
        config.read('config.ini')
        logger.info(f"{config.sections()}")

        self.namespace = config.get('configurations', 'project_name')
        logger.info(f"Selected namespace is : {self.namespace}")

        self.cluster = config.get('configurations', 'cluster')
        logger.info(f"Cluster in which deployment is present is :{self.cluster}")
        
    
    def main(self):
        global cpd_route
        cpd_route = self.get_cpd_route()
        credentials = login.get_credentials(self.namespace)
        logger.info(f"Credentials fetched from secrets: {credentials}")

        baseldap_username = credentials.get("ldapUsername")
        baseldap_password = credentials.get("ldapPassword")

        secondldap_username = credentials.get("ldap2Username")
        secondldap_password = credentials.get("ldap2Password")

        cpadmin_username = credentials.get("admin_username")
        cpadmin_password = credentials.get("admin_password")
        
        logger.info(f"IBM provided credentials (cpadmin only): Username: {cpadmin_username}")
        logger.info(f"IBM provided credentials (cpadmin only) Password: {cpadmin_password}")
        logger.info(f"Base LDAP Username: {baseldap_username}")
        logger.info(f"Base LDAP Password: {baseldap_password}")
        logger.info(f"Additional LDAP Credentials : Username: {secondldap_username}")
        logger.info(f"Additional LDAP Credentials: Password: {secondldap_password}")


        self.onboard_users_to_zen(cpadmin_username,cpadmin_password,secondldap_username)
        self.provide_nav_admin_access_to_new_usr(baseldap_username,baseldap_password,secondldap_username)
        self.provide_objectstore_access_to_new_usr(baseldap_username,baseldap_password,secondldap_username)
        
    
    def get_cpd_route(self):
        """
        Method name: get_cpd_route
        Author: Nusaiba
        Description: Fetch cpd route
        Parameters: None
        Returns:
            cpd route
        """
        cpd_route = f"https://cpd-{self.namespace}.apps.{self.cluster}.cp.fyre.ibm.com"
        logger.info(f"cpd route is : {cpd_route}")
        return cpd_route


    def onboard_users_to_zen(self,cpadmin_username,cpadmin_password,secondldap_username):
        """
        Method name: onboard_users_to_zen
        Author: Nusaiba
        Automates the process of onboarding an additional LDAP user to IBM IM/Zen 
        by logging in as the cpadmin user and navigating through the access control settings.
        Parameters: 
            cpadmin_username (str): IBM provided credentials (cpadmin only) username.
            cpadmin_password (str): IBM provided credentials (cpadmin only) password.
            secondldap_username (str): Username of the additional LDAP user to be onboarded.
        Returns:None
        """
        
        logger.info(f"cpd_route: {cpd_route} (type: {type(cpd_route)})")
        self.driver.get(cpd_route)
        try:
            logger.info("Attempting to select Cpadmin login element")
            self.driver.find_element(By.CLASS_NAME, locators.LocatorElements.cpadmin).click()
        except Exception as e:
            logger.info(f"Failed to select Cpadmin login element.")
            logger.info("Attempting to select Cpadmin login from dropdown...")
            dropdown_element = self.driver.find_element(By.ID,"login_options")
            select = Select(dropdown_element)
            select.select_by_visible_text("IBM provided credentials (cpadmin only)")
        try:
            logger.info(f"Entering username and password : {cpadmin_username} / {cpadmin_password}")
            self.driver.find_element(By.ID, locators.LocatorElements.acceUsername).send_keys(cpadmin_username)
            self.driver.find_element(By.ID, locators.LocatorElements.accePassword).send_keys(cpadmin_password)
            logger.info("Clicking login button...")
            self.driver.find_element(By.NAME, locators.LocatorElements.loginbtn).click()
            logger.info("Clicked on login button...")
            self.driver.find_element(By.ID, locators.LocatorElements.menu_icon).click()
            logger.info("Clicked on menu icon...")
            element = self.wait.until(EC.element_to_be_clickable((By.ID, locators.LocatorElements.administration)))
            element.click()
            logger.info("Clicked on Administration...")
            self.driver.find_element(By.ID, locators.LocatorElements.access_control).click()
            logger.info("Clicked on Access control...")
            self.driver.find_element(By.ID, locators.LocatorElements.add_user).click()
            logger.info("Clicked on Add User + ")
            self.driver.find_element(By.ID, locators.LocatorElements.input_user_text_box).send_keys(secondldap_username)
            logger.info("Provided user to add")
            self.wait.until(EC.element_to_be_clickable((By.XPATH,locators.LocatorElements.selected_user))).click()
            logger.info("Clicked on selected User")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.next_button))).click()
            logger.info("Clicked on Next Button")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.next_button))).click()
            logger.info("Clicked on Next Button")
            self.driver.find_element(By.XPATH,locators.LocatorElements.administrator_access_ckechbox).click()
            logger.info("Checked Administrator role checkbox")
            self.driver.find_element(By.XPATH,locators.LocatorElements.automation_administrator_access_checkbox).click()
            logger.info("Checked Automation Administrator role checkbox")
            self.driver.find_element(By.XPATH,locators.LocatorElements.automation_analyst_access_checkbox).click()
            logger.info("Checked Automation analyst role checkbox")
            self.driver.find_element(By.XPATH,locators.LocatorElements.automation_developer_access_checkbox).click()
            logger.info("Checked Automation Developer role checkbox")
            self.driver.find_element(By.XPATH,locators.LocatorElements.automation_operator_access_checkbox).click()
            logger.info("Checked Automation Operator role checkbox")
            self.driver.find_element(By.XPATH,locators.LocatorElements.user_access_checkbox).click()
            logger.info("Checked Zen User role checkbox")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.next_button))).click()
            logger.info("Clicked on Next Button")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.add_button))).click()
            logger.info("Clicked on Add Button")
            logger.info(f"Onboarded {secondldap_username} to Zen successfully!")
            self.driver.close()
        except Exception as e:
            logger.error(f"Failed to add user to IM {e}")

    def provide_nav_admin_access_to_new_usr(self,baseldap_username,baseldap_password,secondldap_username):
        """
        Method name: Provide_nav_admin_access_to_new_usr
        Author: Nusaiba
        Description: Grants navigator admin access to additional user.
        Parameters: 
            baseldap_username (str): Username for Base LDAP credentials.
            baseldap_password (str): Password for Base LDAP credentials.
            secondldap_username (str): Username of the additional user to be granted access.
        Returns:None
        """

        nav = NavigatorCMOD()
        nav_driver = nav.login_to_navigator(baseldap_username,baseldap_password)
        nav.navigate_to_administration()
        wait = WebDriverWait(nav_driver, 60)
        
        try:
            wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.nav_settings))).click()
            logger.info("Clicked on Settings...")
            wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, "dijitDialogUnderlay")))
            wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.nav_admin_in_settings))).click()
            logger.info("Clicked on Administrators in settings...")
            input_field = wait.until(EC.visibility_of_element_located((By.XPATH, locators.LocatorElements.nav_input_user_text_box )))
            nav_driver.execute_script("arguments[0].removeAttribute('readonly');", input_field)
            input_field.click()
            input_field.send_keys(secondldap_username)
            logger.info(f"Provided {secondldap_username} as user to add...")
            wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.nav_add_button))).click()
            logger.info("Clicked on Add Button...")
            wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.save_close_btn))).click()
            logger.info("Clicked on Save and Close Button...")
        except Exception as e:
            logger.error(f"Failed to provide navigator admin access to the additional ldap user {e}")

    def provide_objectstore_access_to_new_usr(self,baseldap_username,baseldap_password,secondldap_username):
            """
            Method name: Provide_nav_admin_access_to_new_usr
            Author: Nusaiba
            Description: Grants object store access to an additional LDAP user.
            Parameters: 
                baseldap_username (str): Username for Base LDAP credentials.
                baseldap_password (str): Password for Base LDAP credentials.
                secondldap_username (str): Username of the additional user to be granted access.
            Returns:None
            """
            
            cpe = CpeAdmin()
            cpe_driver = cpe.login(baseldap_username,baseldap_password)
            wait = WebDriverWait(cpe_driver, 60)

            try:
                wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.objectstorefolder))).click()
                logger.info("Clicked on object stores folder...")
                wait.until(EC.element_to_be_clickable((By.LINK_TEXT, locators.LocatorElements.objectstoreselection))).click()
                logger.info("Clicked on object store OS01...")
                wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.security_tab))).click()
                logger.info("Clicked on Security tab...")
                wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.add_permissions))).click()
                logger.info("Clicked on Add Permissions...")
                wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.add_usr_or_grp_prmsns))).click()
                logger.info("Clicked on Add User or group Permissions...")
                input_usr = wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.search_input_text_box)))
                input_usr.send_keys(secondldap_username)
                logger.info(f"{secondldap_username} provided as user to to add...")
                wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.search_button))).click()
                logger.info("Clicked on search button...")
                user_elements = cpe_driver.find_elements(By.XPATH, locators.LocatorElements.usr_to_add)

                for index, element in enumerate(user_elements):
                    user_text = element.text
                    logger.info(f"User {index + 1}: {user_text}")
                    
                    if user_text == secondldap_username:
                        element.click()
                        logger.info(f"Clicked on {user_text}")
                        break
            
                button = wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.right_arrow)))
                cpe_driver.execute_script("arguments[0].click();", button)
                logger.info("Clicked on -> Arrow ...")
                wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.ok_button))).click()
                logger.info("Clicked on Ok button...")
                wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.save_button))).click()
                logger.info("Clicked on Save button...")
            except Exception as e:
                logger.error(f"Failed to provide object store access to the additional ldap user {e}")

if __name__ == "__main__":
    multildap_bvt_config = MultildapBVTConfigs()
    multildap_bvt_config.main()