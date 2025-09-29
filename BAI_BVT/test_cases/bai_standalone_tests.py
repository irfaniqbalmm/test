import sys
import os
# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import time, json
from termcolor import colored
from tomlkit import parse
from pathlib import Path
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementNotInteractableException
import inputs.locators as locators
from BAI_BVT.bai_utils.bai_bvt_status import update_bai_status
import BAI_BVT.bai_utils.bai_logs as get_logs
import utils.capture_screenshot as capture_screenshot
from BAI_BVT.driver.launch_driver import ChromeDriverSingleton
from bai_exception import BAIBVTException
from utils.logger import logger

class Test:

    def __init__(self):
        """
        Method name: __init__
        Author: Dhanesh
        Description: Initializes the WebDriver with specified options and settings.
        Parameters:
            None
        Returns:
            None
        """
        with open("./BAI_BVT/resources/config.toml","r") as file :
            self.config = parse(file.read())
        
        self.kube_admin_username = self.config['credentials']['kube_admin_username']
        self.kube_admin_password = self.config['credentials']['kube_admin_password']
        self.username = self.config['credentials']['app_login_username']
        self.password = self.config['credentials']['app_login_password']
        self.screenshot_path = self.config['paths']['screenshot_path']
        self.ocp = self.config['ocp_paths']['ocp']
        self.config_maps = self.config['ocp_paths']['config_maps']
        self.secrets = self.config['ocp_paths']['secrets']
        self.download_path = self.config['paths']['download_path']

        self.driver = ChromeDriverSingleton()

    def verify_installed_operators(self):
        """
        Method name: verify_installed_operators
        Author: Dhanesh
        Description: Navigate to Installed Operators section in OCP and checks if all are successful
        Parameters:
            None
        Returns:
            installed_op_status : Status of the installed operators - PASSED/FAILED
        """
        print("Navigate to BAI deployment Installed Operators section in OCP and checks if all are successful")
        installed_op_status = "FAILED"
        try : 
            self.driver.get(self.ocp)
            try :
                WebDriverWait(self.driver,40).until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.kube_login))).click() 
            except:
                print("KUBE LOGIN NOT FOUND")
                pass
            username_input = WebDriverWait(self.driver, 60).until(EC.element_to_be_clickable((By.ID, locators.LocatorElements.kube_uname)))
            password_input = WebDriverWait(self.driver,60).until(EC.element_to_be_clickable((By.ID, locators.LocatorElements.kube_pwd)))

            username_input.send_keys(self.kube_admin_username)
            password_input.send_keys(self.kube_admin_password)

            login_button = WebDriverWait(self.driver,60).until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.kube_Admin_login)))
            login_button.click()
            WebDriverWait(self.driver,60).until(EC.visibility_of_element_located((By.XPATH,locators.LocatorElements.installed_op)))
            WebDriverWait(self.driver,60).until(EC.visibility_of_element_located((By.XPATH,locators.LocatorElements.installed_check)))
            capture_screenshot.capture_ocp_ss(self.driver,'content-scrollable',"installed_operators", './BAI_BVT/resources/config.toml')
            html_content = self.driver.page_source
            soup = BeautifulSoup(html_content, 'html.parser')

            # Find all rows in the table
            rows = soup.select('.ReactVirtualized__VirtualGrid__innerScrollContainer tr[data-test-rows="resource-row"]')
            operator_sucess = True
            print("Installed operators : ",end = "")
            for row in rows:
                # Extract the status text from each row
                status_element = row.select_one('.co-clusterserviceversion-row__status [data-test="status-text"]')
                status_text = status_element.text.strip()
                # Check if the operator status is "Succeeded"
                if status_text.lower() == 'succeeded':
                    continue
                else:
                    print(colored("FAILED","red"))
                    installed_op_status = "FAILED"
                    operator_sucess = False
                    break
            if operator_sucess :
                print(colored("PASSED","green"))
                installed_op_status = "PASSED"
        except Exception as e : 
            print(print(colored("FAILED","red")), e)
        update_bai_status("OCP_installed_operators",installed_op_status)
        return installed_op_status

    def verify_access_info_config_map(self):
        """
        Method name: verify_access_info_config_map
        Author: Dhanesh
        Description: Navigate to configmaps in OCP and captures the access info configmap
            None
        Returns:
            access_config_status : Status of the configmaps - PASSED/FAILED
        """
        try:
            print("Navigate to configmaps in OCP and captures the access configmap")
            access_config_status = "FAILED"
            self.driver.get(self.config_maps)

            #Login to ocp
            try :
                WebDriverWait(self.driver,40).until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.kube_login))).click() 
            except:
                print("KUBE LOGIN NOT FOUND")
                pass
            username_input = WebDriverWait(self.driver, 60).until(EC.element_to_be_clickable((By.ID, locators.LocatorElements.kube_uname)))
            password_input = WebDriverWait(self.driver,60).until(EC.element_to_be_clickable((By.ID, locators.LocatorElements.kube_pwd)))
            username_input.send_keys(self.kube_admin_username)
            password_input.send_keys(self.kube_admin_password)
            login_button = WebDriverWait(self.driver,60).until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.kube_Admin_login)))
            login_button.click()

            partial_text = "access-info"
            try :
                name = WebDriverWait(self.driver,30).until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.name)))
                name.click()
                name.clear()
                name.send_keys("access-info")
            except :
                print("Couldn't send keys")
            time.sleep(2)
            access_config = WebDriverWait(self.driver,30).until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, partial_text)))
            access_config.click()
            print("Access configmap : ",end="")
            if access_config :
                print(colored("PASSED","green"))
                access_config_status = "PASSED"
            else:
                print(colored("FAILED","red"))
                access_config_status = "FAILED"
            WebDriverWait(self.driver, 30).until(lambda d: d.execute_script('return document.readyState') == 'complete')
            WebDriverWait(self.driver,30).until(EC.presence_of_element_located((By.XPATH, locators.LocatorElements.ocp_scrollable_content)))
            WebDriverWait(self.driver,30).until(EC.presence_of_element_located((By.XPATH, locators.LocatorElements.ocp_data)))
            WebDriverWait(self.driver,30).until(EC.presence_of_element_located((By.XPATH, locators.LocatorElements.configmap_details)))
            time.sleep(2)
            capture_screenshot.capture_ocp_ss(self.driver,'content-scrollable',"access_configmaps", './BAI_BVT/resources/config.toml')
            update_bai_status("OCP_access_configmaps",access_config_status)
            return access_config_status
        
        except Exception as e:
            logger.info(f'Failed to verify bai access info config map')
            update_bai_status("OCP_access_configmaps",access_config_status)

    
    def verify_bai_login(self, dashboard_count):
        """
        Method name: verify_bai_login
        Author: Dhanesh
        Description: Login to the bai dashboard and verify login is successful 
        Parameters:
            dashboard_count: The count of the expected dashboards
        Returns:
            None
        """
        logger.info("==========================================Starting execution of BAI-BPC dashboard login==========================================")
        # Load the endpoints.json file
        logger.info("Loading ./BAI_BVT/resources/endpoints.json file...")
        with open('./BAI_BVT/resources/endpoints.json', 'r') as json_file:
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
        if self.verify_dashboard_count(dashboard_count):
            bai_dashboard_login = "PASSED"
            print(colored("PASSED","green"))
            logger.info('Sucessfully logged into the bai-bpc dashboard')
        else:
            bai_dashboard_login = "FAILED"
            print(colored("FAILED","red"))
            logger.error('Failed to log into the bai-bpc dashboard')
        self.driver.save_screenshot(f'{self.screenshot_path}/bai_bpc_dashboard.png')
        update_bai_status("bai_bpc_dashboard_login",bai_dashboard_login)
        logger.info("==========================================Execution completed for BAI-BPC dashboard login==========================================")
    
    def verify_dashboard_count(self, count):
        """
        Method name: verify_dashboard_count
        Author: Dhanesh
        Description: To verify the count of the dashboards present
        Parameters:
            count: The count of the expected dashboards
        Returns:
            flag: True/False
        """
        flag = False
        try: 
            WebDriverWait(self.driver,60).until(EC.presence_of_element_located((By.ID, locators.LocatorElements.bai_header_id)))
            bai_dashboard_element = WebDriverWait(self.driver,60).until(EC.visibility_of_element_located((By.ID, locators.LocatorElements.bai_header_id)))
            WebDriverWait(self.driver, 60).until(lambda driver: bai_dashboard_element.text != "Fetching dashboard")
            WebDriverWait(self.driver, 60).until(EC.text_to_be_present_in_element((By.ID, locators.LocatorElements.bai_header_id), bai_dashboard_element.text))
            bai_dashboard_count = bai_dashboard_element.text
            if bai_dashboard_count == f'Dashboards ({count})':
                logger.info(f'The dashboards count is expected: {bai_dashboard_count}')
                dashboard_count_status = "PASSED"
                print(colored("PASSED","green"))
                flag = True
            else:
                logger.error(f'The dashboards count is not expected: {bai_dashboard_count}')
                dashboard_count_status = "FAILED"
                print(colored("FAILED","red"))
            update_bai_status("bai_bpc_dashboard_count",dashboard_count_status)
            return flag
        except TimeoutException as e:
            logger.error(f"Timeout occurred while waiting for the dashboard count: {str(e)}")
            print(colored("Timeout error occurred while waiting for the dashboard count.", "red"))
            update_bai_status("bai_bpc_dashboard_count", "FAILED")

        except NoSuchElementException as e:
            logger.error(f"Element not found: {str(e)}")
            print(colored("Element not found error occurred while verifying the dashboard count.", "red"))
            update_bai_status("bai_bpc_dashboard_count", "FAILED")
    
    def search_dashboard(self, dashboard_name):
        """
        Method name: search_dashboard
        Author: Dhanesh
        Description: To search for a specific dashboard and verify the dashboard is present
        Parameters:
            dashboard_name: The name of the expected dashboard to verify
        Returns:
            None
        """
        try:
            logger.info(f'Verifying the dashboard {dashboard_name} is present in the bai-bpc')
            WebDriverWait(self.driver,60).until(EC.presence_of_element_located((By.ID, locators.LocatorElements.bai_dashboard_search_id)))
            bai_dashboard_search_element = WebDriverWait(self.driver,60).until(EC.element_to_be_clickable((By.ID, locators.LocatorElements.bai_dashboard_search_id)))
            bai_dashboard_search_element.send_keys(dashboard_name)
            bai_dashboard_element = locators.LocatorElements.bai_dashboard_name_xpath
            bai_dashboard_element = bai_dashboard_element.replace('[DASHBOARD_NAME]', dashboard_name)
            WebDriverWait(self.driver,60).until(EC.presence_of_element_located((By.XPATH, bai_dashboard_element)))
            WebDriverWait(self.driver,60).until(EC.visibility_of_element_located((By.XPATH, bai_dashboard_element)))
            logger.info(f'The dashboard {dashboard_name} is present in the bai-bpc')
            return True
        except TimeoutException as e:
            logger.info(f'Error verifying the dashboard {dashboard_name} in the bai-bpc: {e}')
            return False

    def verify_content_dashboard(self):
        """
        Method name: verify_content_dashboard
        Author: Dhanesh
        Description: To verify the content dashboard and its data
        Parameters:
            None
        Returns:
            None
        """
        logger.info("==========================================Verifying content dashboard==========================================")
        bai_status = "FAILED"
        try:
            logger.info('Opening content dashboard...')
            if self.search_dashboard('Content Dashboard'):
                content_dashboard_link = WebDriverWait(self.driver,60).until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.content_db_link)))
                logger.info("Content dashboard link located. Attempting to click...")
                content_dashboard_link.click()
                logger.info("Successfully navigated to the content dashboard.")
            else:
                logger.error('Unable to search for the content dashboard')
                self.driver.save_screenshot(f'{self.screenshot_path}/bai_content_dashboard.png')
                update_bai_status("BAI_Content_Dashboard", bai_status)
                return
        except TimeoutException as e:
            logger.error(f"Timeout occurred while waiting for the content dashboard link: {str(e)}")
    
        except NoSuchElementException as e:
            logger.error(f"Element not found: {str(e)}")
    
        except ElementNotInteractableException as e:
            logger.error(f"Element not interactable: {str(e)}")

        try :
            logger.info("Verifying the content dashboard...")
            try : 
                logger.info("Checking for matching images of No data available error...")
                matching_images = self.driver.find_element(By.XPATH, f'//img[@src="{locators.LocatorElements.bai_src_to_check}"]')
                if matching_images :
                    logger.warning("Matching images found to NO DATA AVAILABLE error. Marking BAI status as FAILED.")
                    self.driver.save_screenshot(f'{self.screenshot_path}/bai_content_dashboard.png')
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
                    logger.error(f"bai status is : {bai_status}")
            self.driver.save_screenshot(f'{self.screenshot_path}/bai_content_dashboard.png')
        except Exception as e :
            logger.error(f"An exception occured during taking screenshots : {e}")
            bai_status = "FAILED"
        update_bai_status("BAI_Content_Dashboard", bai_status)
        logger.info(f"BAI Content Dashboard status updated to: {bai_status}")
        return bai_status
    
    def verify_navigator_dashboard(self):
        """
        Method name: verify_navigator_dashboard
        Author: Dhanesh
        Description: To verify the navigator dashboard and its data
        Parameters:
            None
        Returns:
            None
        """
        logger.info("==========================================Verifying navigator dashboard==========================================")
        self.driver.back()
        time.sleep(3)
        nav_status = "FAILED"
        if self.search_dashboard('Navigator Dashboard'):
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
                    self.driver.save_screenshot(f'{self.screenshot_path}/bai_navigator_dashboard.png')
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
        else:
            logger.error('Unable to search for the content dashboard')
            self.driver.save_screenshot(f'{self.screenshot_path}/bai_navigator_dashboard.png')
            update_bai_status("BAI_Navigator_Dashboard", nav_status)
            return
        update_bai_status("BAI_Navigator_Dashboard",nav_status)
    
    def verify_opensearch(self):
        """
        Method name: verify_opensearch
        Description: Login to opensearch and verify the opensearch
        Parameters:
            None
        Returns:
            None
        """
        print("Login to opensearch and load the opensearch page")
        with open('./BAI_BVT/resources/endpoints.json','r') as json_file :
            endpoints = json.load(json_file)
        opensearch_url = endpoints.get("opensearch_url")
        self.driver.get(opensearch_url)
        opensearch_status = "FAILED"
        n=0
        while(n<2) :
            try : 
                WebDriverWait(self.driver,30).until(EC.presence_of_element_located((By.XPATH,'//div[@class=\'json-formatter-container\']')))
                print("Opensearch/elasticsearch UI Loaded without any errors.")
                opensearch_status = "PASSED"
                break
            except Exception as e: 
                print(e)
                n = n+1
                print(f"Try {n} : ",end="")
                print(colored(opensearch_status,"red"))
                self.driver.execute_script("window.open('','_blank');")
                self.driver.switch_to.window(self.driver.window_handles[-1])
                self.driver.get(opensearch_url)
                continue
        time.sleep(2)
        total_height = self.driver.execute_script("return document.body.scrollHeight")
        required_height = total_height*2
        self.driver.set_window_size(1920, int(required_height))
        self.driver.save_screenshot(f'{self.screenshot_path}/opensearch.png')
        update_bai_status("Opensearch",opensearch_status)
        print("Opensearch : ",opensearch_status)
    
    def verify_access_info_contents(self):
        """
        Method name: verify_access_info_contents
        Author: Dhanesh
        Description: To verify the contents inside the bai-bai-access-info
        Parameters:
            None
        Returns:
            exception if any
        """
        logger.info("==========================================Starting execution of veryfing bai-bai-access-info==========================================")
        file_path = './BAI_BVT/resources/endpoints.json'
        access_info_contents = "FAILED"
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
        except FileNotFoundError as e:
            logger.error(f"The file at {file_path} does not exist.")
            raise BAIBVTException(f"The file at {file_path} does not exist.", e)
        except json.JSONDecodeError as e:
            logger.error(f"The file at {file_path} is not a valid JSON.")
            print(colored("FAILED","red"))
            raise BAIBVTException(f"The file at {file_path} is not a valid JSON.", e)
        
        # Check for any None values (null values in JSON)
        for key, value in data.items():
            if value is None:
                logger.error(f"Found None (null) value for key: {key}")
                print(colored("FAILED","red"))
        
        logger.info("All values are properly defined.")
        print(colored("PASSED","green"))
        access_info_contents = "PASSED"
        update_bai_status("access_info_contents",access_info_contents)
        logger.info("==========================================Ended execution of verifying values in bai-bai-access-info==========================================\n\n")

    def verify_bai_operator_log(self):
        """
        Method name: verify_bai_operator_log
        Author: Dhanesh
        Description: To verify the bai operator log has any errors
        Parameters:
            None
        Returns:
            exception if any
        """
        try:
            logger.info("==========================================Starting execution of downloading bai operator logs and checking for errors==========================================")
            logger.info("Trying to get bai operator logs ...")
            get_logs.get_bai_operator_logs()

            # Check for errors in logs
            log_path = Path(self.download_path, 'logs' , 'bai_operator_log_latest.txt')
            errors_present = get_logs.check_log_errors(log_path)
            if errors_present:
                logs_status = "Errors present in logs!"
            else: 
                logs_status = "PASSED - No errors present in logs!"
            update_bai_status("Logs",logs_status)

        except Exception as e:
            logger.error(f'Error ocuured while verifying log: {e}')

if __name__=='__main__':
    test = Test()
    test.verify_access_info_config_map()
    test.verify_access_info_contents()
    test.verify_bai_login(15)
    test.verify_installed_operators()
    test.verify_content_dashboard()
    test.verify_navigator_dashboard()
    test.verify_opensearch()
    test.verify_bai_operator_log()



