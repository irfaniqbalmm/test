import os
import sys
import time

import configparser
from bs4 import BeautifulSoup
from tomlkit import parse
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import inputs.locators as locators
import utils.capture_screenshot as capture_screenshot
from utils.bvt_status import update_status
from utils.logger import logger

class OCP:
    installed_op_status = "FAILED"
    access_config_status = "FAILED"
    init_config_status = "FAILED"
    verify_config_status = "FAILED"

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
        with open("./inputs/config.toml","r") as file :
            self.config = parse(file.read())
        
        self.username = self.config['credentials']['app_login_username']
        self.password = self.config['credentials']['app_login_password']
        self.kube_admin_username = self.config['credentials']['kube_admin_username']
        self.kube_admin_password = self.config['credentials']['kube_admin_password']
        self.screenshot_path = self.config['paths']['screenshot_path']
        self.deployment_type = self.config['configurations']['deployment_type']
        self.ocp = self.config['ocp_paths']['ocp']
        self.config_maps = self.config['ocp_paths']['config_maps']
        self.secrets = self.config['ocp_paths']['secrets']

        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--incognito")
        chrome_options.add_argument('--ignore-certificate-errors')
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.maximize_window()
        self.driver.implicitly_wait(10)

    def navigate_to_installed_operators(self):
        """
        Method name: navigate_to_installed_operators
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Navigate to Installed Operators section in OCP and checks if all are successful
        Parameters:
            None
        Returns:
            installed_op_status : Status of the installed operators - PASSED/FAILED
        """
        logger.info("Navigate to Installed Operators section in OCP and checks if all are successful")
        installed_op_status = "FAILED"
        try : 
            self.driver.get(self.ocp)
            try :
                logger.info(f"Waiting for the kube login option to be clickable.")
                WebDriverWait(self.driver,40).until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.kube_login))).click() 
                logger.info("Clicked on kube login")
            except:
                logger.info("Kube login is not found")
                pass

            logger.info(f"Waiting for the username and password fields to be clickable.")
            username_input = WebDriverWait(self.driver, 60).until(EC.element_to_be_clickable((By.ID, locators.LocatorElements.kube_uname)))
            password_input = WebDriverWait(self.driver,60).until(EC.element_to_be_clickable((By.ID, locators.LocatorElements.kube_pwd)))

            username_input.send_keys(self.kube_admin_username)
            password_input.send_keys(self.kube_admin_password)
            logger.info(f"Send the kube login credentials as: {self.kube_admin_username}/{self.kube_admin_password}")

            logger.info(f"Waiting for the login button to be clickable.")
            login_button = WebDriverWait(self.driver,60).until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.kube_Admin_login)))
            login_button.click()
            logger.info("Clicked on login button.")
            logger.info("Waiting for the visibility of installed operators tab.")
            WebDriverWait(self.driver,60).until(EC.visibility_of_element_located((By.XPATH,locators.LocatorElements.installed_op)))
            logger.info("Installed Operators tab is visible.")
            logger.info("Waiting for the visibility of installed operators checking element.")
            WebDriverWait(self.driver,60).until(EC.visibility_of_element_located((By.XPATH,locators.LocatorElements.installed_check)))
            logger.info("Installed Operators checking element is visible.")
            logger.info("Capturing scrollable screenshot")
            capture_screenshot.capture_ocp_ss(self.driver, 'content-scrollable', "installed_operators")
            logger.info("Validating all operator statuses are 'Succeeded'.")
            html_content = self.driver.page_source
            soup = BeautifulSoup(html_content, 'html.parser')
            # Find all rows in the table
            rows = soup.select('.ReactVirtualized__VirtualGrid__innerScrollContainer tr[data-test-rows="resource-row"]')
            operator_sucess = True
            for row in rows:
                # Extract the status text from each row
                status_element = row.select_one('.co-clusterserviceversion-row__status [data-test="status-text"]')
                status_text = status_element.text.strip()
                # Check if the operator status is "Succeeded"
                if status_text.lower() == 'succeeded':
                    continue
                else:
                    installed_op_status = "FAILED"
                    operator_sucess = False
                    break
            if operator_sucess :
                installed_op_status = "PASSED"
        except Exception as e : 
            logger.exception(f"An exception occured while capturing the installed operators: {str(e)}")
        update_status("OCP_installed_operators",installed_op_status)
        return installed_op_status
    

    def navigate_to_config_maps(self):
        """
        Method name: navigate_to_config_maps
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Navigate to configmaps in OCP and captures the access configmaps
            None
        Returns:
            access_config_status : Status of the configmaps - PASSED/FAILED
        """
        logger.info("Navigate to configmaps in OCP and captures the access, init & verify configmaps")
        logger.info("Opening a new window")
        self.driver.execute_script("window.open('', '_blank');")
        logger.info("Switching to the new window")
        self.driver.switch_to.window(self.driver.window_handles[-1])
        logger.info("Loading the configmaps in the new window")
        self.driver.get(self.config_maps)
        partial_text = "access-info"
        try :
            logger.info("Waiting for the 'name' to be clickable")
            name = WebDriverWait(self.driver,30).until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.name)))
            name.click()
            name.clear()
            name.send_keys("access-info")
        except Exception as e:
            logger.exception(f"An exception occured while sending keys: {e}")
        time.sleep(2)
        access_config = WebDriverWait(self.driver,30).until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, partial_text)))
        access_config.click()
        if access_config :
            access_config_status = "PASSED"
        else:
            access_config_status = "FAILED"
        logger.info("Waiting until the page is fully loaded.")
        WebDriverWait(self.driver, 30).until(lambda d: d.execute_script('return document.readyState') == 'complete')
        logger.info("Waiting for the presence of ocp scroller")
        WebDriverWait(self.driver,30).until(EC.presence_of_element_located((By.XPATH, locators.LocatorElements.ocp_scrollable_content)))
        WebDriverWait(self.driver,30).until(EC.presence_of_element_located((By.XPATH, locators.LocatorElements.ocp_data)))
        logger.info("Waiting for the presence of configmap data")
        WebDriverWait(self.driver,30).until(EC.presence_of_element_located((By.XPATH, locators.LocatorElements.configmap_details)))
        time.sleep(2)
        logger.info("Capturing access-info screenshots")
        capture_screenshot.capture_ocp_ss(self.driver,'content-scrollable',"access_configmaps")
        update_status("OCP_access_configmaps", access_config_status)
        return access_config_status
    
    def capture_init_cm(self):
        """
        Method name: capture_init_cm
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Captures the init configmaps
            None
        Returns:
            init_config_status : Status of the init configmap - PASSED/FAILED
        """
        logger.info("Navigating back")
        self.driver.back()
        time.sleep(10)
        n=0
        while n<3 : 
            init_partial_text = "initialization-config"
            try :
                try :
                    logger.info("Waiting for the clear button to be clickable")
                    clear = WebDriverWait(self.driver,15).until(EC.element_to_be_clickable((By.XPATH, '//button[contains(@id, \'remove_pf-random-id\') and @aria-label=\'close\']')))
                    clear.click()
                    logger.info("Clicked on the clear button.")
                except Exception as e:
                    logger.warning(f"Couldn't find close button: {e}")
                time.sleep(1)
                logger.info("Waiting for the 'name' field to be clickable")
                name = WebDriverWait(self.driver,30).until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.name)))
                name.click()
                logger.info("Clicked on the name field")
                name.clear()
                logger.info("Cleared the name field")
                name.send_keys("initialization")
                logger.info("Send name as 'initialization'")
                time.sleep(2)
            except Exception as e:
                logger.exception(f"an exception occured while trying to send keys: {str(e)}")
            try:
                logger.info("Waiting till the init access info cm is clickable")
                init = WebDriverWait(self.driver,60).until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, init_partial_text)))
                logger.info("Scrolling into view of init cm")
                self.driver.execute_script("arguments[0].scrollIntoView(true);", init)
                init = WebDriverWait(self.driver,60).until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, init_partial_text)))
                init.click()
                logger.info("Clicked on the init configmap.")
                break
            except Exception as e:
                logger.exception(f"An exception occured while trying to find init cm: {str(e)}")
                n+=1
                logger.info("Refreshing the page for another try")
                self.driver.refresh()
                continue
        try : 
            nav_bai_emitter_element_text = 'True'
            nav_app_discovery_plugin_registered_element_text = 'True'
            nav_platform_conn_created_element_text = 'True'
            nav_platform_conn_with_context_element_text = 'True'
            nav_platform_plugin_registered_element_text = 'True'
            nav_walkme_plugin_registered_element_text = 'True'
            logger.info("Waiting for the presence of CPE init")
            cpe_init_element = WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.XPATH, locators.LocatorElements.cpe_init))).text
            logger.info(f"Obtained CPE init value: {cpe_init_element}")
            logger.info("Waiting for the presence of CSS init")
            css_init_element = WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.XPATH, locators.LocatorElements.css_init))).text
            logger.info(f"Obtained CSS init value: {css_init_element}")
            logger.info("Waiting for the presence of Navigator init")
            nav_init_element = WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.XPATH, locators.LocatorElements.nav_init))).text
            logger.info(f"Obtained Navigator init value: {nav_init_element}")
            try :
                logger.info("Waiting for the presence of Navigator BAI init")
                nav_bai_init_element = WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.XPATH, locators.LocatorElements.nav_bai_plugin))).text
                logger.info(f"Obtained Navigator BAI init value: {nav_bai_init_element}")
            except TimeoutException as e:
                    # If element is not found, it will probably be earlier versions
                    nav_bai_init_element = 'True'
                    logger.exception(f"An exception occured while trying to get Navigator BAI init: {e}")
            if self.deployment_type == 'starter' :
                try :
                    logger.info("Waiting for the presence of Navigator BAI emitter init")
                    nav_bai_emitter_element = WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.XPATH,locators.LocatorElements.nav_bai_emitter)))
                    nav_bai_emitter_element_text = nav_bai_emitter_element.text
                    logger.info(f"Obtained Navigator BAI emitter init value: {nav_bai_emitter_element_text}")
                except TimeoutException as e:
                    logger.exception(f"An exception occured while trying to get Navigator BAI emitter init: {e}")
                try :
                    logger.info("Waiting for the presence of Navigator Discovery Plugin init")
                    nav_app_discovery_plugin_registered_element = WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.XPATH,locators.LocatorElements.nav_app_discovery_plugin_registered)))
                    nav_app_discovery_plugin_registered_element_text = nav_app_discovery_plugin_registered_element.text
                    logger.info(f"Obtained Navigator Discovery Plugin init value: {nav_app_discovery_plugin_registered_element_text}")
                except TimeoutException as e:
                    logger.exception(f"An exception occured while trying to get Navigator Discovery Plugin init: {e}")
                try :
                    logger.info("Waiting for the presence of Navigator Platform Connection Creation init")
                    nav_platform_conn_created_element = WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.XPATH,locators.LocatorElements.nav_platform_conn_created)))
                    nav_platform_conn_created_element_text = nav_platform_conn_created_element.text
                    logger.info(f"Obtained Navigator Platform Connection Creation init value: {nav_platform_conn_created_element_text}")
                except TimeoutException as e:
                    logger.exception(f"An exception occured while trying to get Navigator Platform Connection Creation init: {e}")
                try :
                    logger.info("Waiting for the presence of Navigator Platform Connection with Context init")
                    nav_platform_conn_with_context_element = WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.XPATH,locators.LocatorElements.nav_platform_conn_with_context)))
                    nav_platform_conn_with_context_element_text = nav_platform_conn_with_context_element.text
                    logger.info(f"Obtained Navigator Platform Connection with Context init value: {nav_platform_conn_with_context_element_text}")
                except TimeoutException as e:
                    logger.exception(f"An exception occured while trying to get Navigator Platform Connection with Context init: {e}")
                try :
                    logger.info("Waiting for the presence of Navigator Platfrom Plugin registered init")
                    nav_platform_plugin_registered_element = WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.XPATH,locators.LocatorElements.nav_platform_plugin_registered)))
                    nav_platform_plugin_registered_element_text = nav_platform_plugin_registered_element.text
                    logger.info(f"Obtained Navigator Platfrom Plugin registered init value: {nav_platform_plugin_registered_element_text}")
                except TimeoutException as e:
                    logger.exception(f"An exception occured while trying to get Navigator Platfrom Plugin registered init: {e}")
                try :
                    logger.info("Waiting for the presence of Navigator Walkme Plugin registered init")
                    nav_walkme_plugin_registered_element = WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.XPATH,locators.LocatorElements.nav_walkme_plugin_registered)))
                    nav_walkme_plugin_registered_element_text = nav_walkme_plugin_registered_element.text
                    logger.info(f"Obtained Navigator Walkme Plugin registered init value: {nav_walkme_plugin_registered_element_text}")
                except TimeoutException as e:
                    logger.exception(f"An exception occured while trying to get Navigator Walkme Plugin registered init: {e}")
            init_elements = [cpe_init_element,css_init_element,nav_init_element,nav_bai_init_element,nav_bai_emitter_element_text,nav_app_discovery_plugin_registered_element_text,nav_platform_conn_created_element_text,nav_platform_conn_with_context_element_text,nav_platform_plugin_registered_element_text,nav_walkme_plugin_registered_element_text]
            logger.info(f"Checking for init elements: {init_elements}")
            init_boolean_elements = [i == 'True' for i in init_elements]
            if all(init_boolean_elements) :
                logger.info("All init elements passed.")
                init_config_status = "PASSED"
            else :
                logger.info("Init elements check failed.")
                init_config_status = "FAILED" 
        except Exception as e:
            logger.error(f"An exception occured while verifying the init elements: {e}")
            init_config_status = "FAILED"
        capture_screenshot.capture_ocp_ss(self.driver, 'content-scrollable', "initialization_configmaps")
        update_status("OCP_init_configmap", init_config_status)
        return init_config_status
    
    def capture_verify_cm(self):
        """
        Method name: capture_verify_cm
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Captures the verify configmaps
            None
        Returns:
            verify_config_status : Status of the verify configmap - PASSED/FAILED
        """
        logger.info("Navigating back")
        self.driver.back()
        time.sleep(10)
        n=0
        while n < 3 :
            try :
                try :
                    logger.info("Waiting for the clear button to be clickable")
                    clear = WebDriverWait(self.driver, 15).until(EC.element_to_be_clickable((By.XPATH, '//button[contains(@id, \'remove_pf-random-id\') and @aria-label=\'close\']')))
                    clear.click()
                    logger.info("Clicked on the clear button.")
                except Exception as e:
                    logger.warning(f"Couldn't find close button: {e}")
                time.sleep(1)
                logger.info("Waiting for the 'name' field to be clickable")
                name = WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.name)))
                name.click()
                logger.info("Clicked on the name field")
                name.clear()
                logger.info("Cleared the name field")
                name.send_keys("verification")
                logger.info("Send keys as: verification")
                time.sleep(2)
            except Exception as e:
                logger.exception(f"an exception occured while trying to send keys: {str(e)}")
            
            try :
                verify_partial_text = "verification-config"
                logger.info("Waiting till the verify access info cm is clickable")
                verify = WebDriverWait(self.driver, 60).until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, verify_partial_text)))
                logger.info("Scrolling into view of verify cm")
                self.driver.execute_script("arguments[0].scrollIntoView(true);", verify)
                time.sleep(2)
                verify.click()
                logger.info("Clicked on the verify configmap.")
                break
            except Exception as e:
                logger.exception(f"An exception occured while trying to find init cm: {str(e)}")
                n+=1
                logger.info("Refreshing the page for another try")
                self.driver.refresh()
                continue
        time.sleep(5)
        try : 
            nav_verify_element_text = 'True'
            logger.info("Waiting for the presence of CMIS verify")
            cmis_verify_text = WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.XPATH, locators.LocatorElements.cmis_verify))).text
            logger.info(f"Obtained CMIS verify value: {cmis_verify_text}")
            logger.info("Waiting for the presence of CPE verify")
            cpe_verify_text = WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.XPATH, locators.LocatorElements.cpe_verify))).text
            logger.info(f"Obtained CPE verify value: {cpe_verify_text}")
            logger.info("Waiting for the presence of CSS verify")
            css_verify_text = WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.XPATH, locators.LocatorElements.css_verify))).text
            logger.info(f"Obtained CSS verify value: {css_verify_text}")

            if self.deployment_type != 'starter' :
                logger.info("Waiting for the presence of Navigator verify")
                nav_verify_element_text = WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.XPATH, locators.LocatorElements.nav_verify))).text
                logger.info(f"Obtained Naviagtor verify value: {nav_verify_element_text}")

            verify_elements = [cmis_verify_text, cpe_verify_text, css_verify_text, nav_verify_element_text]
            logger.info(f"Checking for verify elements: {verify_elements}")
            verify_boolean_elements = [v == 'True' for v in verify_elements]
            if all(verify_boolean_elements) :
                logger.info("All verify elements passed.")
                verify_config_status = "PASSED"
            else : 
                logger.info("Verify elements check failed.")
                verify_config_status = "FAILED"
        except Exception as e:
            logger.error(f"An exception occured while verifying the verify elements: {e}")
            verify_config_status = "FAILED"
        capture_screenshot.capture_ocp_ss(self.driver, 'content-scrollable', "verification_configmaps")
        update_status("OCP_verify_configmap", verify_config_status)
        return verify_config_status
    
    def take_screenshot(self,filename):
        """
        Method name: take_screenshot
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Takes screenshot
        Parameters:
            filename : file where screenshot is saved
        Returns:
            None
        """
        self.driver.get_screenshot_as_file(filename)
    
    def get_secret_value(self, secret_name, keys):
        """
        Method name: get_secret_value
        Description: To get the secret values based on the input
        Parameters:
            secret_name(string) : The secret name to be used
            keys(list): The keys of the secret username and password in the secret in order
        Returns:
            values(list): List of secrets
        """

        try:
            secrets = self.secrets
            secrets = secrets.replace('secret_name', secret_name)
            logger.info("Opening a new window")
            self.driver.execute_script("window.open('', '_blank');")
            logger.info("Switching to the new window")
            self.driver.switch_to.window(self.driver.window_handles[-1])
            logger.info(f"Loading the url: {secrets}")
            self.driver.get(secrets)
            logger.info(f"Waiting for the presence of reveal values element")
            reveal_button = WebDriverWait(self.driver, 60).until(EC.presence_of_element_located((By.XPATH, locators.LocatorElements.reveal_value_element)))
            self.driver.execute_script("arguments[0].scrollIntoView(true);", reveal_button)
            logger.info("Scrolling into view of reveal values button")
            reveal_button = WebDriverWait(self.driver, 60).until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.reveal_value_element)))
            reveal_button.click()
            logger.info("Clicked on reveal values button")
            values = []
            for key in keys:
                secret_element = locators.LocatorElements.secret_element.replace('<key>', key)
                logger.info("Waiting for the presence of secret elements")
                WebDriverWait(self.driver,30).until(EC.presence_of_element_located((By.XPATH, secret_element)))
                logger.info("Getting secret values")
                values.append(WebDriverWait(self.driver,30).until(EC.visibility_of_element_located((By.XPATH, secret_element))).text.strip())
            return values
        except Exception as e:
            logger.exception(f'Unable to fetch the secret name: {e}')
            return False
    
    def replace_secrets(self):
        """
        Method name: replace_secrets
        Description: To replace the secrets in the testdata.config file
        Parameters:
            none
        Returns:
            None
        """
        try:
            fncm_values = self.get_secret_value('ibm-fncm-secret', ['appLoginUsername', 'appLoginPassword'])
            logger.info(f"The fncm secret values are: {fncm_values}")
            fncm_username = fncm_values[0]
            fncm_password = fncm_values[1]
            iam_values = self.get_secret_value('ibm-iam-bindinfo-platform-auth-idp-credentials', ['admin_username', 'admin_password'])
            logger.info(f"The IAM secret values are: {iam_values}")
            iam_admin_username = iam_values[0]
            iam_admin_password = iam_values[1]
            current_dir = os.getcwd()
            config_path = os.path.join(current_dir, 'oc_operations', 'config', 'testdata.config')

            parser = configparser.ConfigParser(interpolation=None)
            parser.read(config_path)
            parser['EXPECTED_RESULTS']['fncm_username'] = fncm_username
            parser['EXPECTED_RESULTS']['fncm_password'] = fncm_password
            parser['EXPECTED_RESULTS']['iam_admin_username'] = iam_admin_username
            parser['EXPECTED_RESULTS']['iam_admin_password'] = iam_admin_password
            with open(config_path, 'w') as configfile:
                parser.write(configfile)
            logger.info("Successfully updated testdata.config")
        except Exception as e:
            logger.exception(f"An exception occured while trying to update testdata.config with fncm and idp credentials: {str(e)}")

    def close_browser(self) :
        """
        Method name: close_browser
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Closes the browser after execution
        Parameters:
            None
        Returns:
            None
        """
        self.driver.quit()
    
if __name__ == "__main__":
    ocp = OCP()
    ocp.navigate_to_installed_operators()
    ocp.navigate_to_config_maps()
    ocp.capture_init_cm()
    ocp.capture_verify_cm()
    ocp.replace_secrets()
    ocp.close_browser()

