import datetime
import json
import os
import platform
import sys
import time

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from tomlkit import parse

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from component_pages.navigator.nav_cmod import NavigatorCMOD
from component_pages.utilities.check_files_in_directory import file_exists_in_directory
from component_pages.utilities.create_plugin import CreatePlugin
from component_sanity_tests.exceptions.iccsap_exception import ICCSAPSanityTestException
from component_sanity_tests.exceptions.ier_exception import IERSanityTestException
from component_sanity_tests.utils.common_utils.browser_manager import BrowserManager
from component_sanity_tests.utils.common_utils.utilily_scripts import check_logs
from component_sanity_tests.utils.iccsap.copy_file_to_pod import copy_file_to_pod
from component_sanity_tests.utils.common_utils.highlighter import highlighter
from inputs.locators import LocatorElements
from utils.bvt_status import update_status
from utils.logger import logger
from utils.login import fetch_and_decode_secret

class ICN:
    def __init__(self, product, config_file):
        """
        Method name: __init__
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Initializes the ICN class
        Parameters:
            None
        Returns:
            None
        """
        with open(config_file, "r") as file :
            self.config = parse(file.read())

        self.product = product
        self.config_file = config_file
        self.namespace = self.config['configurations']['project_name']
        self.username = self.config['credentials']['app_login_username']
        self.password = self.config['credentials']['app_login_password']
        self.screenshot_path = self.config[product.lower()]['screenshot_path']
        self.download_path = self.config[product.lower()]['download_path']
        self.highlighter = highlighter(screenshot_dir=self.screenshot_path)

        with open('./inputs/endpoints.json','r') as json_file :
            endpoints = json.load(json_file)

        self.taskmanager_route = endpoints.get("taskmanager_route")
        self.iccsap_files_route = endpoints.get("iccsap_files_route")
        self.navigator_route = endpoints.get("navigator_route")

        # Navigator class object
        self.nav = NavigatorCMOD(product, config_file)        

    def login_and_navigate_to_administration(self):
        """
        Method name: login_and_navigate_to_administration
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Logins and navigate to Administration page of ICN
        Parameters:
            None
        Returns:
            None
        """
        try :
            self.nav_driver = self.nav.login_to_navigator()
            self.nav.navigate_to_administration()
        except Exception as e :
            if "ICCSAP" == self.product:
                raise ICCSAPSanityTestException("Failed during login and navigate to Administration") from e
            elif "IER" == self.product:
                raise IERSanityTestException("Failed during login and navigate to Administration") from e
            
    def navigate_to_section_in_icn(self, route, section_selector):
        """
        Method description: Navigates to a specific section in the application using a given selector.
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Args:
            driver (selenium.webdriver.remote.webdriver.WebDriver): The WebDriver instance used to control the browser.
            route: Url to be loaded
            section_selector (str): The XPath selector for the desired section to navigate to.
        Returns:
            None
        """
        logger.info(f"Navigating to {section_selector} page")
        n=0
        while n<3 :
            try :
                WebDriverWait(self.nav_driver, 90).until(EC.presence_of_element_located((By.XPATH, LocatorElements.navigator_slide_drawer_icon))).click()
                logger.info("Clicked on slide drawer icon.")
                break
            except :
                n += 1
                self.nav_driver.execute_script("window.open('','_blank');")
                self.nav_driver.switch_to.window(self.nav_driver.window_handles[-1])
                self.nav_driver.get(route)
                continue
        time.sleep(5)
        while(True):
            try:
                WebDriverWait(self.nav_driver, 10).until(EC.visibility_of_element_located((By.XPATH, section_selector))).click()
                logger.info(f"Clicked on {section_selector} option.")
                break
            except Exception as e:
                logger.error(f"An error occured while trying to click the {section_selector} option : {e}")
                logger.info("Retrying ...")
                WebDriverWait(self.nav_driver, 10).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.navigator_slide_drawer_icon))).click()
                logger.info("Clicked on slide drawer icon.")
            
    def create_plugin(self):
        """
        Method name: create_plugin
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Create the plugin in Navigator
        Parameters:
            None
        Returns:
            None
        """
        try:
            create_plugin = CreatePlugin(self.config_file, self.product)
            plugin_creation = create_plugin.create_plugin(self.nav_driver, self.nav.navigator_route, self.product)
            self.nav_driver.save_screenshot(f"{self.screenshot_path}/{self.product.lower()}_plugin.png")
            self.nav_driver.maximize_window()
        except Exception as e:
            if "ICCSAP" == self.product:
                raise ICCSAPSanityTestException(f"Failed during {self.product} plugin creation", cause=e) from e
            elif "IER" == self.product:
                raise IERSanityTestException("Failed during IER plugin creation", cause=e) from e
        finally:
            update_status("plugin_creation", plugin_creation, self.product)
        
    def create_product_repo(self, repo_name, product_repo_locator, os_name):
        """
        Method name: create_iccsap_repo
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Creates the product repository in the Navigator.
        Parameters:
            repo_name: Name of the repo to create
            product_repo_locator: Locato of the product repo type
            os_name: object store name to which the repo is connected to
        Returns:
            None
        Raises:
            ICCSAPSanityTestException: If fails during ICCSAP repo creation
        """
        try :
            server_url = "https://content-cpe-stateless-svc:9443/wsi/FNCEWS40MTOM/"
            server_locator = LocatorElements.server_url_field
            repository_creation = self.nav.create_repo(self.nav.driver, repo_name, product_repo_locator, server_url, server_locator, self.username, self.password, os_name)
            logger.info("Repository creation returned: %s", repository_creation)
            try:
                repo_locator = LocatorElements.repo_locator.replace("{repo_name}", repo_name)
                logger.info(f"Repo locator XPath: {repo_locator}")
                repo_element=WebDriverWait(self.nav_driver, 60).until(EC.visibility_of_element_located((By.XPATH, repo_locator)))
                screenshot_path = self.highlighter.highlight_element(self.nav_driver, repo_element, testcase_name=f"{repo_name.lower()}_repository")
                logger.info(f"Screenshot saved at: {screenshot_path}")
            except Exception as e :
                logger.exception("Error while locating repository element or taking screenshot")
                raise

        except Exception as e:
            if "ICCSAP" == self.product:
                raise ICCSAPSanityTestException("Failed during ICCSAP repo creation", cause=e) from e
            elif "IER" == self.product:
                raise IERSanityTestException("Failed during IER repo creation", cause=e) from e
        finally:
            if repository_creation:
                update_status("repository_creation", "PASSED", self.product)
            else:
                update_status("repository_creation", "FAILED", self.product)

    def create_product_desktop(self, desktop_name, product_repo):
        """
        Method name: create_product_desktop
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Creates the product desktop in the Navigator.
        Parameters:
            desktop_name : Name of desktop to be created
            product_repo :  Repo connected to the desktop
        Returns:
            created_product_desktop (boolean) : True if desktop is created, False otherwise
        """
        created_product_desktop = False
        try:
            created_product_desktop = self.nav.create_desktop(desktop_name, product_repo)
            WebDriverWait(self.nav_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.desktop_icon))).click()
            logger.info("Navigated to desktops page")
            try:
                desktop_locator = LocatorElements.desktop_locator.replace("{desktop_name}", desktop_name)
                desktop_element=WebDriverWait(self.nav.driver, 60).until(EC.visibility_of_element_located((By.XPATH, desktop_locator)))
                screenshot_path = self.highlighter.highlight_element(self.nav.driver, desktop_element, testcase_name=f"{desktop_name.lower()}_desktop")
                logger.info(f"Screenshot saved at: {screenshot_path}")
            except Exception as e :
              logger.exception("Error while locating desktop element or taking screenshot")
              raise  
        except Exception as e:
            created_product_desktop = False
            if self.product == "ICCSAP":
                raise ICCSAPSanityTestException("Failed during ICCSAP desktop creation", cause=e) from e
            elif self.product == "IER":
                raise IERSanityTestException("Failed during IER desktop creation", cause=e) from e
        finally:
            if created_product_desktop:
                update_status("desktop_creation", "PASSED", self.product)
            else:
                update_status("desktop_creation", "FAILED", self.product)
    
    def scroll_to_find_element(self, locator, max_attempts=20, pause=1):
        """
        Method name: scroll_to_find_element
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Scrolls through the webpage to find an element.
        Parameters:
            locator (str): The locator to match the element with.
            max_attempts (int): The maximum number of attempts to scroll and find the element. Default is 20.
            pause (float): The time in seconds to pause between scroll attempts. Default is 1 second.
        Returns:
            object: The found element.
        Raises:
            Exception: If the element is not found after the maximum number of attempts.
        """
        logger.info("Navigating to TM configuration.")
        logger.info(f"Finding the element: {locator}")
        last_height = self.nav_driver.execute_script("return document.body.scrollHeight")
        for _ in range(max_attempts):
            try:
                element = WebDriverWait(self.nav_driver, 5).until(EC.visibility_of_element_located((By.XPATH, locator)))
                self.nav_driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
                logger.info("Found the element! Navigates to TM configuration.")
                return element
            
            except NoSuchElementException:
                logger.info("Element not found. Retrying.")
                self.nav_driver.execute_script("window.scrollBy(0, window.innerHeight);")
                time.sleep(pause)

                new_height = self.nav_driver.execute_script("return window.scrollY + window.innerHeight")
                if new_height >= last_height:
                    break
                last_height = new_height
        raise Exception(f"Element not found after {max_attempts} scrolls.")
    
    def configure_tm(self):
        """
        Method name: configure_tm
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Configures TM in the Navigator.
        Parameters:
            product : Product for which desktop is created
            product_repo :  Repo connected to the desktop
        Returns:
            created_product_desktop (boolean) : True if desktop is created, False otherwise
        """
        configuring_tm_status = "FAILED"
        try:
            logger.info(f"Configuring task manager")

            logger.info(f"Copying ICCSAP Tasks Jar file into tm-deploy pod.")
            if self.product.upper() == "ICCSAP":
                logger.info("Copying the 'iccsapTasks.jar' file to 'tm-deploy' pod")
                iccsap_tasks_jar_file = os.path.join(self.download_path, "iccsapTasks.jar")
                file_name = os.path.basename(iccsap_tasks_jar_file)
                copy_jar_file_status = copy_file_to_pod(iccsap_tasks_jar_file, "tm-deploy", f"/opt/ibm/extTM/{file_name}")
                update_status("adding_iccsap_jar_file_to_tm", copy_jar_file_status, self.product)

            logger.info(f"Waiting for section: 'Settings' to be visible.")
            WebDriverWait(self.nav_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.settings))).click()
            logger.info(f"Clicked on 'Settings' option.")
            WebDriverWait(self.nav_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.logging_tab)))

            # Scrolling to TM configuration
            self.scroll_to_find_element(LocatorElements.tm_config)
            time.sleep(0.3)

            logger.info(f"Waiting for '{LocatorElements.tm_enable}' to be present")
            tm_enable_element = WebDriverWait(self.nav_driver, 30).until(EC.presence_of_element_located((By.XPATH, LocatorElements.tm_enable)))
            logger.info(f"The {LocatorElements.tm_enable} is present")
            if str(tm_enable_element.get_attribute("aria-checked")).lower() != "true": 
                logger.info("TM service is not enabled. Enabling it.")
                tm_enable_element.click()
                logger.info(f"Clicked on '{LocatorElements.tm_enable}'.")

            logger.info(f"Setting TM URL as : {self.taskmanager_route}")
            tm_url_element = WebDriverWait(self.nav_driver, 60).until(EC.element_to_be_clickable((By.XPATH, LocatorElements.tm_url_field)))
            tm_url_element.click()
            tm_url_element.clear()
            tm_url_element.send_keys(self.taskmanager_route)

            if self.product == "ICCSAP":
                log_directory = "/opt/ibm/wlp/usr/servers/defaultServer/logs"
            elif self.product == "IER":
                log_directory = "C:\Program Files\IBM\CP4BATMlogs"
            logger.info(f"Setting TM log directory as: {log_directory}")
            tm_log_directory_element = WebDriverWait(self.nav_driver, 60).until(EC.element_to_be_clickable((By.XPATH, LocatorElements.tm_log_directory)))
            tm_log_directory_element.click()
            tm_log_directory_element.clear()
            tm_log_directory_element.send_keys(log_directory)

            logger.info(f"Setting TM username as: {self.username}")
            tm_username_element = WebDriverWait(self.nav_driver, 60).until(EC.element_to_be_clickable((By.XPATH, LocatorElements.tm_username_field)))
            tm_username_element.click()
            tm_username_element.clear()
            tm_username_element.send_keys(self.username)

            logger.info(f"Setting TM password as: {self.password}")
            tm_password_element = WebDriverWait(self.nav_driver, 60).until(EC.element_to_be_clickable((By.XPATH, LocatorElements.tm_password_field)))
            tm_password_element.click()
            tm_password_element.clear()
            tm_password_element.send_keys(self.password)

            # Saving screenshot
            self.nav_driver.save_screenshot(f"{self.screenshot_path}/tm_config.png")
            logger.info(f"Screenshot saved at: {self.screenshot_path}/tm_config.png")

            logger.info("Waiting for the visibility of 'Save and Close' button")
            WebDriverWait(self.nav_driver, 30).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.save_close_btn)))
            WebDriverWait(self.nav_driver, 30).until(EC.element_to_be_clickable((By.XPATH, LocatorElements.save_close_btn))).click()
            logger.info("Clicked on the 'Save and Close' button")

            logger.info("Closing the information field")
            logger.info("Waiting for the visibility of 'Information' field")
            WebDriverWait(self.nav_driver, 100).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.info_field)))

            logger.info("Waiting for the visibility of 'Information Close' button")
            logger.info("Information popup located")
            WebDriverWait(self.nav_driver, 100).until(EC.visibility_of_element_located((By.XPATH, f'{LocatorElements.info_close_btn}'))).click()
            logger.info("Information popup closed successfully")
            configuring_tm_status = "PASSED"

            configuring_tm_status = "PASSED"
                
        except Exception as e:
            if self.product == "ICCSAP":
                raise ICCSAPSanityTestException(f"Failed during configuring Task Manager in ICN.", cause=e) from e
            elif self.product == "IER":
                raise IERSanityTestException(f"Failed during configuring Task Manager in ICN.", cause=e) from e
                
        finally:
            update_status("configuring_tm", configuring_tm_status, self.product)

    def close_error_and_continue(self):
        """
        Method name: close_error_and_continue
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Closes the error pop-up and continues testing.
        Parameters: None
        Returns: None
        """
        try:
            logger.info("Waiting for the 'Error Close' button to be clickable.")
            WebDriverWait(self.nav_driver, 30).until(EC.element_to_be_clickable((By.XPATH, LocatorElements.iccsap_error_close_btn))).click()
            logger.info("Clicked on the 'Error Close' button.")
        except Exception as e:
            raise Exception(f"Couldn't close error and continue. Error: {e}")
                
    def start_and_verify_server_instance(self):
        """
        Method name: start_and_verify_server_instance
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Starts and verifies the instance server.
        Parameters: None
        Returns: None
        """
        try:
            try:
                logger.info("Waiting for the 'Running' status to be visible.")
                WebDriverWait(self.nav_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.not_running_status_span)))
                logger.info("The 'Running' status is visible.")
                return 
            except Exception as e:
                logger.warning(f"An error occured while waiting for Running status: {e}")
                logger.info("Will try to start the server.")
            
            logger.info("Waiting for the 'Start' button to be clickable.")
            WebDriverWait(self.nav_driver, 60).until(EC.element_to_be_clickable((By.XPATH, LocatorElements.profile_start_button))).click()
            logger.info("Clicked on the 'Start' button.")

            logger.info("Waiting for 'Start Instance' heading to be visible.")
            WebDriverWait(self.nav_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.iccsap_start_instace)))
            
            keystore_password = fetch_and_decode_secret("ibm-iccsap-secret", "keystorePassword", self.namespace)

            logger.info("Waiting for the 'SSL truststore' field to be clickable.")
            ssl_truststore_field = WebDriverWait(self.nav_driver, 60).until(EC.element_to_be_clickable((By.XPATH, LocatorElements.ssl_trustore_password)))
            ssl_truststore_field.click()
            logger.info("Clicked on the 'SSL truststore' field.")
            ssl_truststore_field.send_keys(keystore_password)

            logger.info("Waiting for the 'SSL keystore' field to be clickable.")
            ssl_keystore_field = WebDriverWait(self.nav_driver, 60).until(EC.element_to_be_clickable((By.XPATH, LocatorElements.ssl_keystore_password)))
            ssl_keystore_field.click()
            logger.info("Clicked on the 'SSL truststore' field.")
            ssl_keystore_field.send_keys(keystore_password)

            logger.info("Waiting for the 'User password' field to be clickable.")
            user_password_field = WebDriverWait(self.nav_driver, 60).until(EC.element_to_be_clickable((By.XPATH, LocatorElements.user_password)))
            user_password_field.click()
            logger.info("Clicked on the 'SSL truststore' field.")
            user_password_field.send_keys("file4net!")

            logger.info("Waiting for the 'OS password' field to be clickable.")
            os_password_field = WebDriverWait(self.nav_driver, 60).until(EC.element_to_be_clickable((By.XPATH, LocatorElements.os_password)))
            os_password_field.click()
            logger.info("Clicked on the 'SSL truststore' field.")
            os_password_field.send_keys(self.password)

            time.sleep(3)

            logger.info("Waiting for the 'Start' button to be clickable.")
            WebDriverWait(self.nav_driver, 60).until(EC.element_to_be_clickable((By.XPATH, LocatorElements.ecm_widget_start))).click()
            logger.info("Clicked on the 'Start' button.")

            # Wait for the arch pro to get started
            logger.info("Waiting for the archpro to get started...")
            time.sleep(60)
            n=0
            while (n<3):
                try:
                    logger.info("Waiting for the 'Download' button to be clickable.")
                    WebDriverWait(self.nav_driver, 30).until(EC.element_to_be_clickable((By.XPATH, LocatorElements.download_btn))).click()
                    logger.info("Clicked on the 'Download' button.")
                    break
                except:
                    # check if deamon not starting error
                    logger.info("Waiting for the visibility of Daemon error message.")
                    WebDriverWait(self.nav_driver, 30).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.daemon_message)))
                    logger.inof("Daemon error is viisble.")
                    logger.info("Waiting for the 'Close' button to be clickable.")
                    WebDriverWait(self.nav_driver, 30).until(EC.element_to_be_clickable((By.XPATH, LocatorElements.daemon_error_close_button))).click()
                    logger.info("Clicked on the 'Close' button.")
                    time.sleep(300)
                    # try again after 5 minutes
                    n+=1
            try:
                logger.info("Waiting for the download to be completed.")
                WebDriverWait(self.nav_driver, 60).until(lambda driver: file_exists_in_directory(self.download_path, "archpro_start.log"))
                logger.info("Downloaded archpro start logs.")
                arch_log_path = os.path.join(self.download_path, "archpro_start.log")
                arch_pro_start_text = "ArchPro is fully initialized. Queue processing is enabled now."
                arch_pro_intialized = check_logs(arch_log_path, arch_pro_start_text)
                if arch_pro_intialized:
                    logger.info("ArchPro is fully initialized.")
                else:
                    logger.info("ArchPro is not initialized.")
            except Exception as e:
                logger.error(f"An exception occured while trying to find the downloads : {e}")

            logger.info("Waiting for the 'Close' button to be clickable.")
            WebDriverWait(self.nav_driver, 60).until(EC.element_to_be_clickable((By.XPATH, LocatorElements.log_close_button))).click()
            logger.info("Clicked on the 'Close' button.")

        except Exception as e:
            raise Exception(f"Failed to start the ICCSAP server instance. Error: {e}")

    # This task  is only for ICCSAP product
    def import_and_start_iccsap_server_profile(self, profile_file, desktop_name):
        """
        Method name: import_and_start_iccsap_server_profile
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Import SAP server profile using a configuration file and start a server instance.
        Parameters:
            profile_file :  Configuration file of the server instance
            desktop_name :  ICCSAP desktop name
        Returns: None
        """
        profile_import_status = "FAILED"
        profile_instance_initialization = "FAILED"
        try:
            # Load ICCSAP Desktop in a new tab
            self.iccsap_desktop_url = f"{self.nav.navigator_route}?desktop={desktop_name}"
            self.nav_driver.execute_script("window.open('', '_blank');")
            self.nav_driver.switch_to.window(self.nav_driver.window_handles[-1])
            self.nav_driver.get(self.iccsap_desktop_url)
            logger.info(f"Loading iccsap desktop: {self.iccsap_desktop_url}")
            self.navigate_to_section_in_icn(self.iccsap_desktop_url, LocatorElements.iccsap_app_configuration_feature)

            logger.info("Waiting for 'Manage Collector Server Instances' label to be visible.")
            WebDriverWait(self.nav_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.manage_collector_services)))
            
            logger.info("Finding 'Import' button element")
            import_button = self.nav_driver.find_element(By.ID, "iccHomeTab_import")
            self.nav_driver.execute_script("arguments[0].click();", import_button)
            logger.info("Clicked on 'Import' button.")
            
            logger.info("Waiting for import input element to be available.")
            file_input = WebDriverWait(self.nav_driver, 60).until(EC.presence_of_element_located((By.XPATH, LocatorElements.import_input)))
            self.nav_driver.execute_script("arguments[0].style.display = 'block';", file_input)
            file_input.send_keys(profile_file)
            logger.info(f"Send file input as: {profile_file}")
            time.sleep(2) # Wait for OK button to be clickable without element interception
            WebDriverWait(self.nav_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.ok_button))).click()
            
            time.sleep(3)
            
            logger.info("Waiting for the 'Save' button to be clickable.")
            WebDriverWait(self.nav_driver, 60).until(EC.element_to_be_clickable((By.XPATH, LocatorElements.save_btn))).click()
            logger.info("Clicked on the 'Save' button.")
            profile_import_status = "PASSED"
            self.nav_driver.save_screenshot(f"{self.screenshot_path}/profile_import.png")

            self.start_and_verify_server_instance()

            logger.info("Waiting for 'Manage Collector Server Instances' tab to be clickable.")
            WebDriverWait(self.nav_driver, 60).until(EC.element_to_be_clickable((By.XPATH, LocatorElements.manage_collector_services))).click()
            logger.info("Clicked on the 'Manage Collector Server Instances' tab.")

            logger.info("Waiting for the 'Import' button to be visible.")
            WebDriverWait(self.nav_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.import_button)))

            try:
                logger.info("Waiting for the 'Running' status to be visible.")
                WebDriverWait(self.nav_driver, 30).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.running)))
                profile_instance_initialization = "PASSED"
                self.nav_driver.save_screenshot(f"{self.screenshot_path}/profile_instance.png")
            except (TimeoutException, NoSuchElementException) as e:
                logger.error("Running status was not found!!")
                logger.info("Waiting for the 'Not running' status to be visible.")
                WebDriverWait(self.nav_driver, 30).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.not_running)))
                profile_instance_initialization = "FAILED"

        except Exception as e:
            profile_instance_initialization = "FAILED"
            raise ICCSAPSanityTestException(f"Failed while importing ICCSAP profile in ICN.", cause=e) from e
        
        finally:
            self.nav_driver.save_screenshot(f"{self.screenshot_path}/server_instance.png")
            update_status("importing_profile", profile_import_status, "ICCSAP")
            update_status("profile_instance_initialization", profile_instance_initialization, "ICCSAP")

    # This task  is only for ICCSAP product
    def create_new_archiving_profile(self, profile_name, doc_class, query_path):
        """
        Method name: create_new_archiving_profile
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Create new archiving instance.
        Parameters:
            doc_class  :  Previously creation ICCSAP document class name
            query_path :  Path to scanned documents or description file
        Returns: None
        """
        archiving_profile_creation_status = "FAILED"
        try:
            # Navigate to ICCSAP Application Administration Feature Tab
            self.navigate_to_section_in_icn(self.iccsap_desktop_url, LocatorElements.iccsap_app_administration_feature)
            self.close_error_and_continue()

            logger.info("Waiting for 'Manage Profiles' heading to be visible.")
            WebDriverWait(self.nav_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.manage_profiles)))
            
            logger.info("Waiting for the 'Archiving Profiles' option to be clickable.")
            WebDriverWait(self.nav_driver, 60).until(EC.element_to_be_clickable((By.XPATH, LocatorElements.archiving_profiles))).click()
            logger.info("Clicked on the 'Archiving Profiles' option.")

            logger.info("Waiting for the 'New Archiving Profile' option to be clickable.")
            WebDriverWait(self.nav_driver, 60).until(EC.element_to_be_clickable((By.XPATH, LocatorElements.new_archiving_profile))).click()
            logger.info("Clicked on the 'New Archiving Profile' option.")

            logger.info("Waiting for the 'Archiving Profile Name' field to be available.")
            profile_name_field = WebDriverWait(self.nav_driver, 60).until(EC.presence_of_element_located((By.XPATH, LocatorElements.archiving_profile_name)))
            self.nav_driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", profile_name_field)
            profile_name_field.click()
            profile_name_field.clear()
            profile_name_field.send_keys(profile_name)

            logger.info("Waiting for the 'Collector Server Instance' dropdown to be clickable.")
            WebDriverWait(self.nav_driver, 60).until(EC.element_to_be_clickable((By.XPATH, LocatorElements.collector_server_instance_dropdown))).click()
            logger.info("Clicked on the 'Collector Server Instance' dropdown.")

            logger.info("Waiting for the 'ICCSAP Configuration Instance' option to be clickable.")
            WebDriverWait(self.nav_driver, 60).until(EC.element_to_be_clickable((By.XPATH, LocatorElements.iccsap_config_instance))).click()
            logger.info("Clicked on the 'ICCSAP Configuration Instance' option.")

            host = f"content-iccsap-svc.{self.namespace}.svc"
            host_locator = LocatorElements.host_locator.replace("<host>", host)
            logger.info("Waiting for the 'host' text to be visible.")
            WebDriverWait(self.nav_driver, 60).until(EC.visibility_of_element_located((By.XPATH, host_locator)))
            logger.info("The host is updated.")

            """ 
            This logic runs automatically, so it’s currently commented out. 
            If any issues arise in the future, it can be re-enabled. 

            # logger.info("Waiting for the 'Logical Archive' dropdown to be clickable.")
            # WebDriverWait(self.nav_driver, 60).until(EC.element_to_be_clickable((By.XPATH, LocatorElements.logical_archive_dropdown))).click()
            # logger.info("Clicked on the 'Logical Archive' dropdown.")

            # logger.info("Waiting for the 'Logical Archive' option to be clickable.")
            # WebDriverWait(self.nav_driver, 60).until(EC.element_to_be_clickable((By.XPATH, LocatorElements.logical_archive_option))).click()
            # logger.info("Clicked on the 'Logical Archive' option.")
            """

            logger.info("Waiting for the 'Doc Class' field to be available.")
            sap_doc_class_input = WebDriverWait(self.nav_driver, 60).until(EC.element_to_be_clickable((By.XPATH, LocatorElements.sap_document_input)))
            logger.info("The 'Doc Class' field is available.")
            self.nav_driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", sap_doc_class_input)
            sap_doc_class_input.click()
            sap_doc_class_input.clear()
            sap_doc_class_input.send_keys(doc_class)

            logger.info("Waiting for the 'SAP Directory' field to be available.")
            sap_query_path_input = WebDriverWait(self.nav_driver, 60).until(EC.element_to_be_clickable((By.XPATH, LocatorElements.sap_directory_input)))
            self.nav_driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", sap_query_path_input)
            sap_query_path_input.click()
            sap_query_path_input.clear()
            sap_query_path_input.send_keys(query_path)

            logger.info("Waiting for the 'Save' button to be clickable.")
            WebDriverWait(self.nav_driver, 60).until(EC.element_to_be_clickable((By.XPATH, LocatorElements.archiving_profile_save_btn))).click()
            logger.info("Clicked on the 'Save' button.")

            logger.info("Waiting for the 'Archiving Profiles' tab to be clickable.")
            WebDriverWait(self.nav_driver, 60).until(EC.element_to_be_clickable((By.XPATH, LocatorElements.archiving_profiles_tab))).click()
            logger.info("Clicked on the 'Archiving Profiles' tab.")

            archiving_profile_locator = LocatorElements.archiving_profile_locator.replace("<profile_name>", profile_name)
            logger.info("Waiting for the 'Archiving Profile' created to be visible.")
            WebDriverWait(self.nav_driver, 60).until(EC.visibility_of_element_located((By.XPATH, archiving_profile_locator)))
            logger.info("Created 'Archiving Profile' is visible.")

            archiving_profile_creation_status = "PASSED"

        except Exception as e:
            archiving_profile_creation_status = "FAILED"
            raise ICCSAPSanityTestException("Failed to create new archiving profile.", cause=e) from e
        
        finally:
            self.nav_driver.save_screenshot(f"{self.screenshot_path}/profile_instance.png")
            update_status("archiving_profile_creation", archiving_profile_creation_status, "ICCSAP")

    def schedule_task(self, task_name, profile_name, task_type="run_now"):
        """
        Method name: schedule_task
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Starts and verifies the instance server.
        Parameters:
            task_name: Name of task being scheduled
            profile_name: Name of profile instance used
            task_type: Type of task being scheduled(default=run_now)
        Returns: None
        """
        try:
            logger.info("Waiting for the 'New Archiving Task' option to be clickable.")
            WebDriverWait(self.nav_driver, 60).until(EC.element_to_be_clickable((By.XPATH, LocatorElements.new_archiving_task))).click()
            logger.info("Clicked on the 'New Archiving Task' option.")

            logger.info("Waiting for the 'Task Title' field to be available.")
            task_title_field = WebDriverWait(self.nav_driver, 60).until(EC.element_to_be_clickable((By.XPATH, LocatorElements.task_name_field)))
            logger.info("The 'Task Title' field is available.")
            self.nav_driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", task_title_field)
            task_title_field.click()
            task_title_field.clear()
            task_title_field.send_keys(task_name)

            logger.info("Waiting for the 'Archiving Profile' dropdown to be clickable.")
            WebDriverWait(self.nav_driver, 60).until(EC.element_to_be_clickable((By.XPATH, LocatorElements.archiving_profile_dropdown))).click()
            logger.info("Clicked on the 'Archiving Profile' dropdown.")

            profile_locator = LocatorElements.profile_locator.replace("<profile_name>", profile_name)
            logger.info("Waiting for the profile option to be visible.")
            WebDriverWait(self.nav_driver, 60).until(EC.element_to_be_clickable((By.XPATH, profile_locator))).click()
            logger.info("Clicked on the created profile option.")

            if task_type == "run_now":
                logger.info("Waiting for the 'Save' button to be clickable.")
                WebDriverWait(self.nav_driver, 60).until(EC.element_to_be_clickable((By.XPATH, LocatorElements.archiving_task_save_btn))).click()
                logger.info("Clicked on the 'Save' button.")

            else:
                logger.info("Waiting for the 'Run Once' option to be clickable.")
                WebDriverWait(self.nav_driver, 60).until(EC.presence_of_element_located((By.XPATH, LocatorElements.run_once_option))).click()
                logger.info("Clicked on the 'Run Once' option.")

                today = datetime.date.today()
                formatted_date = today.strftime("%d/%m/%Y")
                current_time = datetime.datetime.now()
                time_plus_2 = current_time + datetime.timedelta(minutes=2)   
                formatted_time = time_plus_2.strftime("%H:%M")
                logger.info("Waiting for the 'Run Once Date' input to be available.")
                date_field = WebDriverWait(self.nav_driver, 60).until(EC.presence_of_element_located((By.XPATH, LocatorElements.run_once_date)))
                date_field.clear()
                date_field.send_keys(formatted_date)
                logger.info(f"Send date as: {formatted_date}")

                logger.info("Waiting for the 'Run Once Time' input to be available.")
                time_field = WebDriverWait(self.nav_driver, 60).until(EC.presence_of_element_located((By.XPATH, LocatorElements.run_once_time)))
                time_field.clear()
                time_field.send_keys(formatted_time)
                logger.info(f"Send time as: {formatted_time}")

                logger.info("Waiting for the 'Save' button to be clickable.")
                WebDriverWait(self.nav_driver, 60).until(EC.element_to_be_clickable((By.XPATH, LocatorElements.archiving_task_save_btn))).click()
                logger.info("Clicked on the 'Save' button.")

        except Exception as e:
            raise Exception(f"Failed to create the {task_type} task: {e}.")

    def check_task_status(self, task_name, ss_name):
        """
        Method name: check_task_status
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Checks the status of the task scheduled
        Parameters:
            task_name: Name of task being scheduled
            ss_name: Name of screenshot captured
        Returns: 
            status: Status of the task scheduled
        """
        status = "FAILED"
        try:
            logger.info("Waiting for the 'Archiving Tasks' option to be clickable.")
            WebDriverWait(self.nav_driver, 60).until(EC.element_to_be_clickable((By.XPATH, LocatorElements.archiving_tasks))).click()
            logger.info("Clicked on the 'Archiving Tasks' option.")

            run_now_task_locator = LocatorElements.run_now_task_locator.replace("<task_name>", task_name)
            logger.info("Waiting for the 'Archiving Task' created to be visible.")
            WebDriverWait(self.nav_driver, 60).until(EC.visibility_of_element_located((By.XPATH, run_now_task_locator)))
            logger.info("Created 'Archiving Profile' is visible.")

            time.sleep(30) #Sleep until the task completes

            logger.info("Waiting for the 'Refresh' button to be clickable.")
            WebDriverWait(self.nav_driver, 60).until(EC.element_to_be_clickable((By.XPATH, LocatorElements.archiving_tasks_refresh_btn))).click()
            logger.info("Clicked on the 'Refresh' button.")

            completed_status_locator = LocatorElements.completed_status_locator.replace("<task_name>", task_name)
            logger.info("Waiting for the 'Completed' status to be visible.")
            WebDriverWait(self.nav_driver, 60).until(EC.visibility_of_element_located((By.XPATH, completed_status_locator)))
            logger.info("Created 'Completed' status is visible.")
            status = "PASSED"

        except Exception as e:
            raise Exception(f"Failed to verify the task {task_name}: {e}.")
        
        finally:
            self.nav_driver.save_screenshot(f"{self.screenshot_path}/{ss_name}.png")
            return status

    def create_archiving_tasks(self, profile_name):
        """
        Method name: create_archiving_tasks
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Creates archiving task using the given profile instance
        Parameters:
            profile_name: Name of profile used to schedule tasks
        Returns: None
        """
        run_now_archiving_task_status = "FAILED"
        run_once_archiving_task_status = "FAILED"
        try:
            self.navigate_to_section_in_icn(self.iccsap_desktop_url, LocatorElements.iccsap_app_operation_feature)

            logger.info("Waiting for 'Manage Tasks' heading to be visible.")
            WebDriverWait(self.nav_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.manage_tasks)))

            logger.info("Waiting for 'Welcome' heading to be visible.")
            WebDriverWait(self.nav_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.iccsap_welcome_tab)))

            WebDriverWait(self.nav_driver, 30).until(lambda d: d.execute_script("return document.readyState") == "complete")
            time.sleep(3) #Wait until page is completely loaded
            
            logger.info("Waiting for the 'Archiving Tasks' option to be clickable.")
            WebDriverWait(self.nav_driver, 100).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.archiving_tasks)))
            WebDriverWait(self.nav_driver, 100).until(EC.element_to_be_clickable((By.XPATH, LocatorElements.archiving_tasks))).click()
            logger.info("Clicked on the 'Archiving Tasks' option.")

            run_now_task_name = "Run now task"
            self.schedule_task(run_now_task_name, profile_name)
            run_now_archiving_task_status = self.check_task_status(run_now_task_name, "archiving_task_run_now")

            run_once_task_name = "Run once task"
            self.schedule_task(run_once_task_name, profile_name, "run_once")
            # Sleep for 2 minutes for the task to be scheduled
            time.sleep(120)
            run_once_archiving_task_status = self.check_task_status(run_once_task_name, "archiving_task_run_once")

        except Exception as e:
            raise ICCSAPSanityTestException("Failed to create archiving tasks.", cause=e) from e
        
        finally:
            update_status("schedule_archiving_tasks_run_now", run_now_archiving_task_status, "ICCSAP")
            update_status("schedule_archiving_tasks_run_once", run_once_archiving_task_status, "ICCSAP")

    def quit_browser(self):
        """
        Method name: quit_browser
        Author: Anisha Suresh
        Description: Quits the browser.
        Parameters: None
        Returns: None
        """ 
        try:
            browser_manager = BrowserManager(self.nav_driver)
            browser_manager.quit_browser()
        except Exception as e:
            if self.product == "ICCSAP":
                raise ICCSAPSanityTestException(f"Failed to quit the navigator browser.", cause=e) from e
    
    def load_desktop(self, desktop_name):
        """
        Method name: load_desktop  
        Author: Nusaiba K K and Anisha Suresh  
        Description: Load the specified desktop (ICN or IER)  
        Parameters:
            desktop_name (str): Name of the desktop to load (e.g., 'ICNDESK', 'IERDESK')  
        Returns: None
        """
        try:
            self.nav_driver.get(f"{self.navigator_route}?desktop={desktop_name}")
            logger.info(f"{desktop_name} Desktop is loading")
            WebDriverWait(self.nav_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.navigator_slide_drawer_icon)))
            self.nav_driver.save_screenshot(f"{self.screenshot_path}/{desktop_name}.png")
            
        except IERSanityTestException as e:
            logger.error(f"{desktop_name} Desktop loading failed: {e}")