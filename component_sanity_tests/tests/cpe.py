from sqlite3 import Time
import time
from types import SimpleNamespace
import os
import sys

from tomlkit import parse
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import TimeoutException, WebDriverException

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from component_pages.cpe.cpe import CpeAdmin
from component_pages.iccsap import ICCSAP
from component_sanity_tests.exceptions.cpe_exception import CPESanityTestException
from component_sanity_tests.exceptions.iccsap_exception import ICCSAPSanityTestException
from component_sanity_tests.tests.acce import ACCE
from component_sanity_tests.tests.icn import ICN
from component_sanity_tests.utils.iccsap import prepare_profile
from inputs.locators import LocatorElements
from utils.bvt_status import update_status
from utils.logger import logger
from component_sanity_tests.utils.common_utils.highlighter import highlighter
import component_sanity_tests.reports.cpe.generate_report as generate_report
import component_sanity_tests.utils.common_utils.create_pdf_report as pdf_report
import component_sanity_tests.utils.common_utils.reset_execution as reset_execution

CONFIG_FILE = "./component_sanity_tests/config/config.toml"
class CPE:

    def __init__(self):
        """
        Method name: __init__
        Author: Nadil Rudhainif (nadil.rudhainif@ibm.com)
        Description: This function is used to initialize the classes and other variables required to run sanity tests for CPE products.
        Parameters:
            None
        Returns
            None
        """
        self.objectstores = "OS01"
        self.args = SimpleNamespace(objectstore=self.objectstores,config_file_path=CONFIG_FILE, product="CPE")
        self.product = self.args.product.upper()
        with open(CONFIG_FILE, "r") as file:
            self.config = parse(file.read())
        self.username = self.config['credentials']['app_login_username']
        self.password = self.config['credentials']['app_login_password']
        self.namespace = self.config['configurations']['project_name']
        self.screenshot_path = self.config[self.args.product.lower()]['screenshot_path']
        self.highlighter = highlighter(screenshot_dir=self.screenshot_path)
        self.cpe = CpeAdmin()
        self.cpe_driver = self.cpe.login(self.username, self.password)
        self.cpe_driver.timeouts.implicit_wait = 180
        self.actions = ActionChains(self.cpe_driver) 
        self.common_variables()   
        self.acce = ACCE(self.args) 
        self.reset_execution_data = reset_execution.ResetExecutionData(self.product)
        
    def check_browser_objectstore_page(self):
        """
        Method name: check_browser_objectstore_page
        Author: Nadil Rudhainif (nadil.rudhainif@ibm.com)
        Description: This function is used to check the browser is in open state and present in Object Store Pagee to continue with the next script.
        Parameters:
            None
        Returns
            None
        """ 
        try:
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.object_store_OS01_root_icon)))
            logger.info("OS01 root icon is already visible. Proceeding...")
        except TimeoutException:
            logger.warning("OS01 root icon not visible. Trying to navigate manually...")
            try:
                WebDriverWait(self.cpe_driver, 30).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.object_store))).click()
                logger.info("Clicked on 'Object Store' button.")
                WebDriverWait(self.cpe_driver, 100).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.object_store_name))).click()
                logger.info("Clicked on 'OS01' button.")
            except TimeoutException as e:
                logger.error("Failed to find or click Object Store or OS01 within timeout.")
                raise
            except Exception as e:
                logger.exception("Unexpected error occurred during object store navigation.")
                raise

    def check_browser_p8domain_page(self):
        """
        Method name: check_browser_p8domain_page
        Author: Nadil Rudhainif (nadil.rudhainif@ibm.com)
        Description: This function is used to check the browser is in open state and present in P8 Domain page to continue with the next script.
        Parameters:
            None
        Returns
            None
        """ 
        try:
            WebDriverWait(self.cpe_driver, 60).until(
                EC.visibility_of_element_located((By.XPATH, LocatorElements.object_store)))
        except TimeoutException:
            print("[WARNING] Object Store not found, proceeding anyway...")
        try:
            WebDriverWait(self.cpe_driver, 60).until(
                EC.visibility_of_element_located((By.XPATH, LocatorElements.os01_close_button))).click()
        except TimeoutException:
            print("[WARNING] Close button not found, proceeding anyway...")
    
    def common_variables(self):
        """
        Method name: check_browser_p8domain_page
        Author: Nadil Rudhainif (nadil.rudhainif@ibm.com)
        Description: This function is used to check the browser is in open state and present in P8 Domain page to continue with the next script.
        Parameters:
            None
        Returns
            None
        """ 
        timestamp = str(int(time.time()))
        # Affinity Group
        self.affgroup_name = "affinitygroup1" + timestamp
        self.created_aff_group = f'//a[contains(text(),"{self.affgroup_name}")]'
        # PreProcessor
        self.pre_processor_name = "PreProcessor" + timestamp
        self.created_preprocessor = f'//span[text()="Change Preprocessor Action: {self.pre_processor_name}"]'
        # Background Class Template
        self.background_class_name = "BSCT" + timestamp
        self.created_bsct= f'//a[contains(text(),"{self.background_class_name}")]' 
        # Choice List Wizard
        self.choice_list_data = "ChoiceList" + timestamp
        self.group_name = "Asia" + timestamp
        self.item_name = "India" + timestamp
        self.created_group =f'//span[contains(text(),"{self.group_name}")]'
        self.created_item = f'//span[contains(text(),"{self.item_name}")]'
        self.created_choicelist= f'//a[contains(text(),"{self.choice_list_data}")]'
        # Sub Folder
        self.parent_folder_name = "ParentFolder" + timestamp
        self.child_folder_name = "ChildFolder" + timestamp
        self.created_parentfolder= f'//span[text()="Folder: {self.parent_folder_name}"]'
        self.created_child_folder = f'//input[contains(@id,"Parent_folder.Properties") and @value="{self.parent_folder_name}"]'
        # Instance Wizard
        self.instance_folder_name = "InstanceFolder" + timestamp
        self.created_folder = f'//span[contains(text(),"{self.instance_folder_name}")]'
        # Document Class
        self.document_folder_name = "DOC" + timestamp
        self.doc_created = f'//input[@value="{self.document_folder_name}"]'
        self.folder_name = "NewFolder" + timestamp
        self.folder_created = f'//input[@value="{self.folder_name}"]'
        self.document=f'//span[text()="{self.document_folder_name}"]'
        self.folder=f'//span[text()="{self.folder_name}"]'
        # Marking Set
        self.markingset_name =  "MarkingSet" + timestamp
        self.markingvalue = "MarkingValue" + timestamp
        self.created_markingset = f'//span[text()="Marking Set: {self.markingset_name}"]'

        # Subscription
        self.subscription_name =  "Subscription" + timestamp
        self.eventname = "Work Flow Event" + timestamp
        self.created_subscriptions = f'//span[text()="Subscription: {self.subscription_name}"]'

        # Document Life Cycle Action
        self.life_cyle_action_name =  "DLCA" + timestamp
        self.created_life_cycle_action = f'//span[text()="Document Lifecycle Action: {self.life_cyle_action_name}"]'

        # Property Template Object
        self.property_template_name = "PropertyTemplate" +timestamp
        self.created_propertytemplate = f'//span[text()="Property Template: {self.property_template_name}"]'
        self.created_propertytemplate_link = f'//a[text()="{self.property_template_name}"]'
        self.search_propertytemplate = f'//td[text()="{self.property_template_name}"]'
        self.added_property_template = f'//label[text()="Display name:"]/ancestor::td/following-sibling::td/descendant::input[@value="{self.property_template_name}"]'
        
         # Property Template
        self.property_templates_name = "PropertyTemplates" +timestamp
        self.created_propertytemplates = f'//span[text()="Property Template: {self.property_templates_name}"]'
        self.created_propertytemplates_link = f'//a[text()="{self.property_template_name}"]'
        self.search_propertytemplates = f'//td[text()="{self.property_template_name}"]'
        self.added_property_templates = f'//label[text()="Display name:"]/ancestor::td/following-sibling::td/descendant::input[@value="{self.property_template_name}"]'

        # Custom Object Wizard
        self.containment_name = "CustomObject" + timestamp
        self.created_custom_object = f'//span[text()="Custom Object: {self.containment_name}"]'

    def check_and_create_security_policy(self):
        """
        Method name: check_and_create_security_policy
        Author: Nadil Rudhainif (nadil.rudhainif@ibm.com)
        Description: This function ensure whether security policy is created, if not create one.
        Parameters:
            None
        Returns
            None
        """
        try:
            WebDriverWait(self.cpe_driver, 150).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.administrativerfolder))).click()
            logger.info("Clicked on 'Global Configuration' Button.")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.security_policy))).click()
            logger.info("Clicked on 'Administration' link.")

            try:
                WebDriverWait(self.cpe_driver, 10).until(
                    EC.visibility_of_element_located((By.XPATH, LocatorElements.security_policy_existing))
                )
                logger.info("Security Policy already exists. Skipping creation.")
            except TimeoutException:
                logger.info("Security Policy not found. Proceeding with creation...")
                WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.security_policy_new_button))).click()
                logger.info("Clicked on New button.")
                WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.security_policy_displayname))).send_keys("TestSecurityPolicy")
                logger.info("Entered security policy name.")
                WebDriverWait(self.cpe_driver, 60).until(EC.element_to_be_clickable((By.XPATH, LocatorElements.security_policy_next_button))).click()
                logger.info("Clicked 'Next' button - Step 1.")
                WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.security_policy_specify_template_text)))
                logger.info("Template text appeared.")

                WebDriverWait(self.cpe_driver, 60).until(EC.element_to_be_clickable((By.XPATH, LocatorElements.security_policy_add_button))).click()
                logger.info("Clicked 'Add' button.")
                WebDriverWait(self.cpe_driver, 60).until(EC.element_to_be_clickable((By.XPATH, LocatorElements.security_policy_add_security_template_text)))
                logger.info("Wait for Security Template Text")
                checkbox1 = WebDriverWait(self.cpe_driver, 10).until(EC.presence_of_element_located((By.XPATH, LocatorElements.security_policy_released_checkbox)))
                if not checkbox1.is_selected():
                    self.cpe_driver.execute_script("arguments[0].click();", checkbox1)
                    logger.info("Clicked Status Released checkbox.")
                checkbox2 = WebDriverWait(self.cpe_driver, 10).until(EC.presence_of_element_located((By.XPATH, LocatorElements.security_policy_reservation_checkbox)))
                if not checkbox2.is_selected():
                    self.cpe_driver.execute_script("arguments[0].click();", checkbox2)
                    logger.info("Clicked Status Reservation checkbox.")
                checkbox3 = WebDriverWait(self.cpe_driver, 10).until(EC.presence_of_element_located((By.XPATH, LocatorElements.security_policy_inprocess_checkbox)))
                if not checkbox3.is_selected():
                    self.cpe_driver.execute_script("arguments[0].click();", checkbox3)
                    logger.info("Clicked Status In Process checkbox.")
                checkbox4 = WebDriverWait(self.cpe_driver, 10).until(EC.presence_of_element_located((By.XPATH, LocatorElements.security_policy_superseded_checkbox)))
                if not checkbox4.is_selected():
                    self.cpe_driver.execute_script("arguments[0].click();", checkbox4)
                    logger.info("Clicked Status Superseded checkbox.")
                WebDriverWait(self.cpe_driver, 60).until(EC.element_to_be_clickable((By.XPATH, LocatorElements.security_policy_ok_button))).click()
                logger.info("Clicked 'OK' button ")
                WebDriverWait(self.cpe_driver, 60).until(EC.element_to_be_clickable((By.XPATH, LocatorElements.security_policy_next_button))).click()
                logger.info("Clicked 'Next' button - Step 2.")
                WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.bsct_summary)))
                logger.info("Summary data is available.")
                WebDriverWait(self.cpe_driver, 60).until(EC.element_to_be_clickable((By.XPATH, LocatorElements.finish_button))).click()
                logger.info("Clicked 'Finish' button.")
                WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.success_text)))
                logger.info("Success message appeared.")
                WebDriverWait(self.cpe_driver, 60).until(EC.element_to_be_clickable((By.XPATH, LocatorElements.subfolder_open_button))).click()
                logger.info("Clicked on 'Open Subfolder' button.")
            time.sleep(2)
            WebDriverWait(self.cpe_driver, 60).until(EC.element_to_be_clickable((By.XPATH, LocatorElements.secruity_policy_close))).click()
            logger.info("Clicked on 'Close' button - Policy.")
            WebDriverWait(self.cpe_driver, 60).until(EC.element_to_be_clickable((By.XPATH, LocatorElements.security_policy_admin_close))).click()
            logger.info("Clicked on 'Close' button - Admin.")

        except Exception as e:
            logger.error(f"check_and_create_security_policy failed: {type(e).__name__}: {e}")
            raise

    def deletion_created_affinity_group(self):
        """
        Method name: deleted_created_affinity_group
        Author: Nadil Rudhainif (nadil.rudhainif@ibm.com)
        Description: This function is used to delete the created affinity group
        Parameters:
            None
        Returns
            None
        """ 
        try:
            wait = WebDriverWait(self.cpe_driver, 60)
            aff_group_elem = wait.until(EC.visibility_of_element_located((By.XPATH, self.created_aff_group)))
            if aff_group_elem.is_displayed():
                aff_group_elem.click()
                logger.info("Clicked on affinity group")
                wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.affinity_action_button))).click()
                logger.info("Clicked on affinity group action")
                wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.delete_affinity_button))).click()
                logger.info("Clicked on delete affinity button")
                wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.ok_button))).click()
                wait.until(EC.invisibility_of_element((By.XPATH, LocatorElements.ok_button)))
                logger.info("Confirmed deletion of affinity group")
                wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.affinity_close_button))).click()
                logger.info("Clicked on 'Affinity Close' button")
                wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.administration_close_button))).click()
                logger.info("Clicked on 'Administration Close' button")
                wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.global_close_button))).click()
                logger.info("Clicked on 'Global Close' button")
        except Exception as e:
                logger.error(f"Error occurred while deleting affinity group: {str(e)}", exc_info=True)
                raise CPESanityTestException("Failed during affinity group deletion sequence") from e   
        
    def create_affinity_group(self):
        """
        Method name: create_affinity_group
        Author: Nadil Rudhainif (nadil.rudhainif@ibm.com)
        Description: This function is used to verify affinity group creation.
        Parameters:
            None
        Returns
            None
        """ 
        try:
            affinity = "FAILED"  
            logger.info(f"Creating affinity groups")
            self.check_browser_p8domain_page()
            logger.info(f"Waiting for section: 'Global Configuration' to be visible.")
            time.sleep(5)
            WebDriverWait(self.cpe_driver, 150).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.globalconfig_button))).click()
            logger.info(f"Clicked on 'Global Configuration' Button.")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.administration_link))).click()
            logger.info(f"Clicked on 'Administration' link.")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.affinitygroups_link))).click()
            logger.info(f"Clicked on 'Affinitygroups' link.")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.new_button))).click()
            logger.info(f"Clicked on 'New' button.")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.affinitygroup_displaynamefield))).send_keys(self.affgroup_name)
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.cpe_next_button))).click()
            logger.info(f"Clicked on 'Next' button.")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.aff_display_name_heading)))
            logger.info(f"waited for display name to be visible.")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.finish_button))).click()
            logger.info(f"Clicked on 'Finish' button.")
            if WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.success_text))).is_displayed():
                logger.info(f"successfully created.")
                affinity = "PASSED"
                WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.close_button))).click()
            else:
                logger.error(f"affinity group creation failed.")
            try:
                WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH,LocatorElements.affinity_close_button))).click()
                logger.info(f"Clicked on close button..")
                time.sleep(5)
                WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.globalconfig_button))).click()
                logger.info(f"Clicked on 'Global Configuration' Button.")
                WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.administration_link))).click()
                WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.affinitygroups_link))).click()
                logger.info(f"Clicked on 'affinity groups' link..")
                created_aff_group_element = WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, self.created_aff_group)))
                logger.info(f"{self.created_aff_group}")
                if created_aff_group_element.is_displayed():
                    logger.info(f"affinity group created successfully.") 
                    screenshot_path = self.highlighter.highlight_element(self.cpe_driver, created_aff_group_element, testcase_name="affinity")
                    print(f"Screenshot saved at: {screenshot_path}")
            except Exception as e:
                raise CPESanityTestException(f"Failed on the creatiion of affinity groups", cause=e) from e
        except Exception as f:
                raise CPESanityTestException(f"Failed during creating affinity groups", cause=f) from f
        finally:
            update_status("affinity", affinity, self.product)
            self.deletion_created_affinity_group()    
    

    def deletion_created_preprocessor(self):
        """
        Method name: deletion_created_preprocessor
        Author: Nadil Rudhainif (nadil.rudhainif@ibm.com)
        Description: This function is used to delete the created preprocessor file
        Parameters:
            None
        Returns
            None
        """ 
        try:
                wait = WebDriverWait(self.cpe_driver, 60)
                preprocessor_elem = wait.until(EC.visibility_of_element_located((By.XPATH, self.created_preprocessor)))
                if preprocessor_elem.is_displayed():
                    logger.info("Deleting the created class file...")
                    wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.processor_action_button))).click()
                    logger.info("Clicked on 'Action' button")
                    wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.processor_action_delete_button))).click()
                    logger.info("Clicked on 'Delete' button")
                    wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.ok_button))).click()
                    logger.info("Clicked on 'OK' button")
                    wait.until(EC.invisibility_of_element((By.XPATH, LocatorElements.ok_button)))
                    logger.info("Confirmation alert disappeared")
                    wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.processor_changepreprocessor_close))).click()
                    logger.info("Clicked on 'Change Pre Processor Close' button")
                    wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.processor_events_close))).click()
                    logger.info("Clicked on 'Events Close' button")
        except Exception as e:
                logger.error(f"Error occurred while deleting the preprocessor: {str(e)}", exc_info=True)
                raise CPESanityTestException("Failed during preprocessor deletion sequence") from e
        
    def change_preprocessor_action(self):
        """
        Method name: change_preprocessor_action
        Author: Nadil Rudhainif (nadil.rudhainif@ibm.com)
        Description: This function is used to verify the change preprocessor action.
        Parameters:
            None
        Returns
            None
        """ 
        try:
            preprocessor = "FAILED"
            logger.info(f"Starting with pre processor action testing.")
            self.check_browser_objectstore_page()
            WebDriverWait(self.cpe_driver, 100).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.events_actions_processes))).click()
            logger.info(f"Clicked on 'Event Actions Processes'. Button")
            WebDriverWait(self.cpe_driver, 100).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.change_processor_action_link))).click()
            logger.info(f"Clicked on 'Change Pre Processor Action'. Link")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.processor_newbutton))).click()
            logger.info(f"Clicked on 'New'. Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.processor_display_name_heading_textfield))).send_keys(self.pre_processor_name)
            logger.info(f"Add 'DisplayName'. Text Field")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.cpe_next_button))).click()
            logger.info(f"Clicked on 'Next'. Button")

            try:
                action_class_text = WebDriverWait(self.cpe_driver, 10).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.change_processor_action_class_text)))
                if action_class_text.is_displayed():
                    logger.info("Waited for 'ActionClass' text.")
                    next_button = WebDriverWait(self.cpe_driver, 10).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.cpe_next_button)))
                    if next_button.is_displayed():
                        next_button.click()
                        logger.info("Clicked on 'Next' button.")
            except TimeoutException:
                logger.warning("'ActionClass' text was not visible within the timeout period. Continuing.")

            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.processor_specify_type_text)))
            logger.info(f"Wait for specify type text")
            logger.info(f"Checking checkbox is selected")
            checkbox = WebDriverWait(self.cpe_driver, 10).until(EC.presence_of_element_located((By.XPATH, LocatorElements.processor_checkbox)))
            if not checkbox.is_selected():
                self.cpe_driver.execute_script("arguments[0].click();", checkbox)
                logger.info("Clicked Status checkbox.")
            radioButton = WebDriverWait(self.cpe_driver, 10).until(EC.presence_of_element_located((By.XPATH, LocatorElements.processor_javascript_radiobutton)))
            if not radioButton.is_selected():
                self.cpe_driver.execute_script("arguments[0].click();", radioButton)
                logger.info("Clicked JavaScript radioButton.")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.cpe_next_button))).click()
            logger.info(f"Clicked on 'Next'. Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.processor_javascript_data)))
            logger.info(f"Waited for Scripts data to be available.")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.cpe_next_button))).click()
            logger.info(f"Clicked on 'Next'. Button")
            try:
                object_property_text = WebDriverWait(self.cpe_driver, 10).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.processor_objectproperties_text)))
                if object_property_text.is_displayed():
                    object_property_text.click()
                    logger.info("Clicked on 'Object Property' text.")
                    next_button = WebDriverWait(self.cpe_driver, 10).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.cpe_next_button)))
                    if next_button.is_displayed():
                        next_button.click()
                        logger.info("Clicked on 'Next' button.")
            except TimeoutException:
                logger.warning("'Object Property' text was not visible within the timeout period. Continuing.")

            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.bsct_summary)))
            logger.info(f"Waited for Summary data to be available.")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.finish_button))).click()
            logger.info(f"Checking for 'Finish'. button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.success_text)))
            logger.info(f"Checking for 'Success'. Message")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.subfolder_open_button))).click()
            logger.info(f"Checking for 'Close'. button")
            created_preprocessor_element=WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, self.created_preprocessor)))
            if created_preprocessor_element.is_displayed():
                logger.info(f"Change pre processors action created successfully'")
                time.sleep(3)
                screenshot_path = self.highlighter.highlight_element(self.cpe_driver, created_preprocessor_element, testcase_name="preprocessor")
                print(f"Screenshot saved at: {screenshot_path}") 
                preprocessor = "PASSED"
            else:
                logger.error(f"Change pre processors action creation failed.")         
        except Exception as f:
                raise CPESanityTestException(f"Failed to change pre processor action.", cause=f) from f
        finally:
            update_status("preprocessor", preprocessor, self.product)
            self.deletion_created_preprocessor()

    def deletion_backgroundsearch(self):
        """
        Method name: deletion_backgroundsearch
        Author: Nadil Rudhainif (nadil.rudhainif@ibm.com)
        Description: This function is used to delete the background search class template
        Parameters:
            None
        Returns
            None
        """ 
        try:
            wait = WebDriverWait(self.cpe_driver, 60)
            bsct_elem = wait.until(EC.visibility_of_element_located((By.XPATH, self.created_bsct)))
            if bsct_elem.is_displayed():
                logger.info("Deleting the created class file...")
                bsct_elem.click()
                logger.info("Clicked on 'Background Search Class Template'")
                wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.bsct_action_button))).click()
                logger.info("Clicked on BSCT action button")
                wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.bcst_delete_button))).click()
                logger.info("Clicked on 'Delete BSCT' button")
                wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.ok_button))).click()
                wait.until(EC.invisibility_of_element((By.XPATH, LocatorElements.ok_button)))
                logger.info("Confirmed deletion of BSCT class")
                wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.bsct_close_button))).click()
                logger.info("Clicked on 'BSCT Close' button")
                wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.bsct_datadesign_close))).click()
                logger.info("Clicked on 'Data Design Close' button")
        except Exception as e:
            logger.error(f"Error occurred while deleting BSCT class: {str(e)}", exc_info=True)
            raise CPESanityTestException("Failed during BSCT class deletion sequence") from e
        
    def create_background_search_class_template(self):
        """
        Method name: create_background_search_class_template
        Author: Nadil Rudhainif (nadil.rudhainif@ibm.com)
        Description: This function is used to verify background search class template creation.
        Parameters:
            None
        Returns
            None
        """
        try:
            classtemplate = "FAILED"
            logger.info(f"Starting with creation of background search class template'.")
            self.check_browser_objectstore_page()
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.bsct_datadesign_button))).click()
            logger.info(f"Clicked on 'Data Design'. Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.bsct_background_search_class_template_button))).click()
            logger.info(f"Clicked on 'Background Search Class Template'. Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.bsct_new_button))).click()
            logger.info(f"Clicked on 'New'. Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.bsct_displayname_textfield))).send_keys(self.background_class_name)
            logger.info(f"Add the 'DisplayName'. TextField")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.bsct_symbolic_name_textfield))).click()
            logger.info(f"Clicked 'Symbolic Name'. TextField")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.instance_next_button))).click()
            logger.info(f"Clicked 'Next'. TextField")
            textfield = WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.bsct_search_expression_textfield)))
            textfield.clear()
            textfield.send_keys("Select DocumentTitle From Document")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.instance_next_button))).click()
            logger.info(f"Clicked 'Next'. TextField")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.bsct_set_search_option))).click()
            logger.info(f"Wait for 'Decide New Or Existing'. TextField")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.instance_next_button))).click()
            logger.info(f"Clicked 'Next'. TextField")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.bsct_decide_new_existing_class))).click()
            logger.info(f"Wait for 'Set Search option'. TextField")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.instance_next_button))).click()
            logger.info(f"Clicked 'Next'. TextField")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.bsct_name_the_search_result_class))).click()
            logger.info(f"Wait for 'Search Result class'. TextField")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.instance_next_button))).click()
            logger.info(f"Clicked 'Next'. TextField")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.bsct_define_search_result_prop))).click()
            logger.info(f"Wait for 'Search Result Properties'. TextField")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.instance_next_button))).click()
            logger.info(f"Clicked 'Next'. TextField")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.bsct_summary))).click()
            logger.info(f"Wait for 'Summary'. TextField")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.finish_button))).click()
            logger.info(f"Clicked 'Finish'. TextField")
            if WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.success_text))).is_displayed():
                logger.info(f"successfully created.")
                WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.close_button))).click()
            else:
                logger.error(f"Background search class template failed.")
            try:
                WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH,LocatorElements.bsct_close_button))).click()
                logger.info(f"Clicked on bsct close button..")
                time.sleep(5)
                WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.bsct_background_search_class_template_button))).click()
                logger.info(f"Clicked on 'Background Search Class Template'. Button")
                created_background_search_element = WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, self.created_bsct)))
                if created_background_search_element.is_displayed():
                    time.sleep(3)
                    logger.info(f"Background search class template created successfully.")
                    classtemplate = "PASSED"
                    screenshot_path = self.highlighter.highlight_element(self.cpe_driver, created_background_search_element, testcase_name="classtemplate")
                    print(f"Screenshot saved at: {screenshot_path}")  
                else:
                    logger.error(f"Background search class template failed to create")   
            except Exception as e:
                raise CPESanityTestException(f"Failed on the creatiion of Background search class template", cause=e) from e                       
        except Exception as f:
                raise CPESanityTestException(f"Failed to create background search class template", cause=f) from f      
        finally:
            update_status("classtemplate", classtemplate, self.product)
            self.deletion_backgroundsearch()

    def deletion_choicelist(self):
        """
        Method name: deletion_choicelist
        Author: Nadil Rudhainif (nadil.rudhainif@ibm.com)
        Description: This function is used to delete the created choice list
        Parameters:
            None
        Returns
            None
        """ 
        try:
            wait = WebDriverWait(self.cpe_driver, 60)
            group_elem = wait.until(EC.visibility_of_element_located((By.XPATH, self.created_group)))
            item_elem = wait.until(EC.visibility_of_element_located((By.XPATH, self.created_item)))
            if group_elem.is_displayed() and item_elem.is_displayed():
                logger.info("Deleting the created class file...")
                wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.choice_action_button))).click()
                logger.info("Clicked on 'Choice Group Action' button")
                wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.choice_delete_button))).click()
                logger.info("Clicked on 'Delete Choice' button")
                wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.ok_button))).click()
                wait.until(EC.invisibility_of_element((By.XPATH, LocatorElements.ok_button)))
                logger.info("Confirmed deletion of Choice List")
                wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.choice_close_button))).click()
                logger.info("Clicked on 'Choice List Close' button")
                wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.bsct_datadesign_close))).click()
                logger.info("Clicked on 'Data Design Close' button")
        except Exception as e:
            logger.error(f"Error occurred while deleting Choice List: {str(e)}", exc_info=True)
            raise CPESanityTestException("Failed during Choice List deletion sequence") from e
        
    def choice_list_wizard(self):
        """
        Method name: choice_list_wizard
        Author: Nadil Rudhainif (nadil.rudhainif@ibm.com)
        Description: This function is used to verify the choice list wizard.
        Parameters:
            None
        Returns
            None
        """
        try:
            choicelist = "FAILED" 
            logger.info(f"Starting with creation of choice list wizard'.")
            self.check_browser_objectstore_page()
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.bsct_datadesign_button))).click()
            logger.info(f"Clicked on 'Data Design'. Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.choice_list_link))).click()
            logger.info(f"Clicked on 'Choice List'. Link")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.choice_new_button))).click()
            logger.info(f"Clicked on 'New'. Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.choice_display_name_textfield))).send_keys(self.choice_list_data)
            logger.info(f"Add the 'DisplayName'. TextField")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.choice_description_textfield))).click()
            logger.info(f"Clicked 'Description'. TextField")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.choice_next_button))).click()
            logger.info(f"Clicked 'Next'. TextField")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.choice_select_text)))
            logger.info(f"Waiting for 'Select'. Text")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.choice_next_button))).click()
            logger.info(f"Clicked 'Next'. TextField")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.choice_new_group))).click()
            logger.info(f"Clicked on 'New Group'.Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.choice_new_display_name))).send_keys(self.group_name)
            logger.info(f"Add 'GroupName'. TextField")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.choice_add_button))).click()
            logger.info(f"Clicked on Add'.Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.choice_ok_button))).click()
            logger.info(f"Clicked 'Ok'. Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.choice_new_item))).click()
            logger.info(f"Clicked 'New Item'. Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.choice_new_display_name))).send_keys(self.item_name)
            logger.info(f"Add 'GroupName'. TextField")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.choice_add_button))).click()
            logger.info(f"Clicked on Add'.Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.choice_ok_button))).click()
            logger.info(f"Clicked 'Ok'. Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.choice_next_button))).click()
            logger.info(f"Clicked 'Next'. TextField")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.bsct_summary))).click()
            logger.info(f"Wait for 'Summary'. TextField")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.finish_button))).click()
            logger.info(f"Clicked 'Finish'. TextField")
            if WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.success_text))).is_displayed():
                logger.info(f"successfully created.")
                WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.close_button))).click()
            else:
                logger.error(f"Choice List creation failed.")
            try:
                WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH,LocatorElements.choice_close_button))).click()
                logger.info(f"Clicked on Choice List Close' Button")
                time.sleep(1)
                WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.choice_list_link))).click()
                logger.info(f"Clicked on 'Choice List'. Link")

                search_filter_tab=WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.choice_list_search_filter)))
                search_filter_tab.send_keys(self.choice_list_data)
                search_filter_tab.send_keys(Keys.ENTER)
                logger.info(f"Search for created 'Choice List' Item ")
                WebDriverWait(self.cpe_driver, 60).until(EC.element_to_be_clickable((By.XPATH, self.created_choicelist))).click()
                logger.info(f"Clicked on 'Created Choice List'. Item")

                time.sleep(2)
                WebDriverWait(self.cpe_driver, 60).until(EC.element_to_be_clickable((By.XPATH, LocatorElements.choice_choiceitems_button))).click()
                logger.info(f"Clicked on 'Choice Items'. Link")
                created_group_element=WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, self.created_group)))
                if (created_group_element.is_displayed() and
                     WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, self.created_item))).is_displayed()):
                        logger.info(f"Choice List created successfully.")
                        screenshot_path = self.highlighter.highlight_element(self.cpe_driver, created_group_element, testcase_name="choicelist")
                        print(f"Screenshot saved at: {screenshot_path}")  
                        choicelist = "PASSED"   
                else:
                        logger.error(f"Choice List creation failed.")
            except Exception as e:
                raise CPESanityTestException(f"Failed on the creation of choice list", cause=e) from e               
        except Exception as f:
                raise CPESanityTestException(f"Failed to create choice list", cause=f) from f
        finally:
            update_status("choicelist", choicelist, self.product)
            self.deletion_choicelist()
            
    def deletion_subfolder(self):
        """
        Method name: deletion_subfolder
        Author: Nadil Rudhainif (nadil.rudhainif@ibm.com)
        Description: This function is used to delete the sub folder.
        Parameters:
            None
        Returns
            None
        """ 
        try:
            wait = WebDriverWait(self.cpe_driver, 60)
            subfolder_elem = wait.until(EC.visibility_of_element_located((By.XPATH, self.created_child_folder)))
            if subfolder_elem.is_displayed():
                logger.info("Deleting the subfolder class file...")
                wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.subfolder_action_button))).click()
                logger.info("Clicked on 'Action' button")
                wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.subfolder_action_delete_button))).click()
                logger.info("Clicked on 'Delete' button")
                wait.until(EC.invisibility_of_element((By.XPATH, LocatorElements.subfolder_action_delete_button)))
                logger.info("Subfolder deletion in progress...")
                wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.subfolder_deletefolder_text)))
                logger.info("Detected 'Deleted Folder' text")
                wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.ok_button))).click()
                logger.info("Clicked on 'OK' button")
                wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.subfolder_browser_close_button))).click()
                logger.info("Clicked on 'Browser Close' button")

        except Exception as e:
            logger.error(f"Error occurred while deleting subfolder: {str(e)}", exc_info=True)
            raise CPESanityTestException("Failed during subfolder deletion sequence") from e  
             
    def create_sub_folder(self):
        """
        Method name: create_sub_folder
        Author: Nadil Rudhainif (nadil.rudhainif@ibm.com)
        Description: This function is used to verify the parent and child folder are getting created or not
        Parameters:
            None
        Returns
            None
        """
        try:
            subfolder = "FAILED"
            parentfolder = "FAILED"
            logger.info(f"Starting with creation of parent and child folder'.")
            self.check_browser_objectstore_page()
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.subfolder_browser))).click()
            logger.info(f"Clicked on 'Browser'. Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.subfolder_root_folder))).click()
            logger.info(f"Clicked on 'Root Folder'. Link")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.subfolder_action_button))).click()
            logger.info(f"Clicked on 'Action'. Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.subfolder_newfolder_button))).click()
            logger.info(f"Clicked 'New Folder'. Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.subfolder_foldername_textfield))).send_keys(self.parent_folder_name)
            logger.info(f"Add 'Folder Name'. TextField")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.subfolder_next_button))).click()
            logger.info(f"Clicked 'Next'. Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.subfolder_object_properties)))
            logger.info(f"Waiting for 'Object Properties'. Text")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.subfolder_next_button))).click()
            logger.info(f"Clicked 'Next'. Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.subfolder_retaining_prop)))
            logger.info(f"Waiting for 'Retaining Propertoes'. Text")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.subfolder_next_button))).click()
            logger.info(f"Clicked 'Next'. Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.bsct_summary))).click()
            logger.info(f"Wait for 'Summary'. TextField")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.finish_button))).click()
            logger.info(f"Clicked 'Finish'. TextField")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.success_text))).is_displayed()
            logger.info(f"successfully created.")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.subfolder_open_button))).click()
            logger.info(self.created_parentfolder)
            created_parent_folder=WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH,self.created_parentfolder)))
            if created_parent_folder.is_displayed():
                logger.info(f"Parent folder got created")
                time.sleep(5)
                screenshot_path = self.highlighter.highlight_element(self.cpe_driver, created_parent_folder, testcase_name="parentfolder")
                print(f"Screenshot saved at: {screenshot_path}")    
                parentfolder = "PASSED"
                update_status("parentfolder", parentfolder, self.product)
            else:
                logger.error(f"Creation of parent folder failed.")
            try:
                if WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH,self.created_parentfolder))).is_displayed():
                    logger.info(f"Creation of sub folder:")
                    time.sleep(5)
                    WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.subfolder_close_root_folder))).click()
                    logger.info(f"Clicked on 'Close'. Button")
                    WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.subfolder_action_button))).click()
                    logger.info(f"Clicked on 'Action'. Button")
                    WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.subfolder_newfolder_button))).click()
                    logger.info(f"Clicked 'New Folder'. Button")
                    WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.subfolder_foldername_textfield))).send_keys(self.child_folder_name)
                    logger.info(f"Add 'Sub Folder Name'. TextField")
                    WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.subfolder_next_button))).click()
                    logger.info(f"Clicked 'Next'. Button")
                    WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.subfolder_object_properties)))
                    logger.info(f"Waiting for 'Object Properties'. Text")
                    WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.subfolder_next_button))).click()
                    logger.info(f"Clicked 'Next'. Button")
                    WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.subfolder_retaining_prop)))
                    logger.info(f"Waiting for 'Retaining Propertoes'. Text")
                    WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.subfolder_next_button))).click()
                    logger.info(f"Clicked 'Next'. Button")
                    WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.bsct_summary))).click()
                    logger.info(f"Wait for 'Summary'. TextField")
                    WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.finish_button))).click()
                    logger.info(f"Clicked 'Finish'. TextField")
                    WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.success_text)))
                    logger.info(f"Waiting for 'Success'. Text")
                    WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.subfolder_open_button))).click()
                    logger.info(f"Waiting for 'Open'. Button")
                    subfolder_close_parent_folder = '//span[contains(text(),"Parent")]/ancestor::span/following-sibling::span[@title="Close"]'
                    WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH,subfolder_close_parent_folder))).click()
                    logger.info(f"Waiting for 'Close'. Button")
                    WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.subfolder_properties_button))).click()
                    logger.info(f"Clicked 'Properties'. Button")
                    created_child_folder_element = WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, self.created_child_folder)))
                    if created_child_folder_element.is_displayed():
                        logger.info(f"Subfolder is successfully got created")  
                        screenshot_path = self.highlighter.highlight_element(self.cpe_driver, created_child_folder_element, testcase_name="subfolder")
                        print(f"Screenshot saved at: {screenshot_path}")    
                        subfolder = "PASSED"
                    else:
                        logger.error(f"Failed to create subfolder")   
            except Exception as e:
                raise CPESanityTestException(f"Failed on the creation of sub folder", cause=e) from e                   
        except Exception as f:
                raise CPESanityTestException(f"Failed to creatioon of parent folder", cause=f) from f   
        finally:
            update_status("subfolder", subfolder, self.product)
            self.deletion_subfolder()
            
    def deletion_instancewizard(self):
        """
        Method name: deletion_instancewizard
        Author: Nadil Rudhainif (nadil.rudhainif@ibm.com)
        Description: This function is used to delete the created instance
        Parameters:
            None
        Returns
            None
        """ 
        try:
            wait = WebDriverWait(self.cpe_driver, 60)
            folder = wait.until(EC.visibility_of_element_located((By.XPATH, self.created_folder)))
            if folder.is_displayed():
                logger.info("Deleting the subfolder class file...")
                wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.instance_close_button))).click()
                logger.info("Clicked on 'Instance Close' button")
                wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.instance_classes_expand))).click()
                logger.info("Clicked on 'Classes Expand' button")
                wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.instance_datadesign_expand))).click()
                logger.info("Clicked on 'Data Design Expand' button")
                wait.until(EC.visibility_of_element_located((By.XPATH, self.created_folder))).click()
                logger.info("Clicked on 'Created Folder'")
                wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.instance_folder_action))).click()
                logger.info("Clicked on 'Action' button")
                wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.instance_folder_delete))).click()
                logger.info("Clicked on 'Delete' button")
                wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.instance_delete_heading)))
                logger.info("Detected 'Deleted Folder' text")
                wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.ok_button))).click()
                logger.info("Clicked on 'OK' button")
                wait.until(EC.invisibility_of_element((By.XPATH, self.created_folder)))
                logger.info("Subfolder deletion in progress...")
                wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.instance_rootfolder_expand))).click()
                logger.info("Clicked on 'Root Folder Expand' button")
                wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.instance_browser_expand))).click()
                logger.info("Clicked on 'Browser Expand' button")

        except Exception as e:
                logger.error(f"Error occurred while deleting folder: {str(e)}", exc_info=True)
                raise CPESanityTestException("Failed during Folder Wizard") from e
        
    def create_instance_wizard(self):
        """
        Method name: create_instance_wizard
        Author: Nadil Rudhainif (nadil.rudhainif@ibm.com)
        Description: This function is used to verify the instance or folder is getting created in rootfolder using folder class
        Parameters:
            None
        Returns
            None
        """
        try:
            instancewizard = "FAILED"
            logger.info(f"Starting with creation of instance wizard'.")
            self.check_browser_objectstore_page()
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.instance_browser_expand))).click()
            logger.info(f"Clicked on 'Browser Expand'. Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.instance_rootfolder_expand))).click()
            logger.info(f"Clicked on 'Root Folder Expand'. Button")
            rootfolder=WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.instance_rootfolder)))
            self.actions.context_click(rootfolder).perform()
            logger.info("Performed right-click on 'Root Folder'.")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.instance_copyobjectstore))).click()
            logger.info(f"Select 'Instance_copyobjectstore'. Option")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.instance_datadesign_expand))).click()
            logger.info(f"Clicked on 'Data Design Expand'. Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.instance_classes_expand))).click()
            logger.info(f"Clicked on 'Classes Expand'. Button")
            folder_class=WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.instance_folder)))
            self.actions.context_click(folder_class).perform()
            logger.info("Performed right-click on 'Folder Class'.")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.instance_createinstance_button))).click()
            logger.info(f"Clicked on 'Action'. DropDown")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.instance_parent_dropdown))).click()
            logger.info(f"Click on 'Drop Down'. Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.instance_dropdown_paste))).click()
            logger.info(f"Click on 'Paste'. Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.instance_parent_textfield))).send_keys(self.instance_folder_name)
            logger.info(f"Add on 'Folder Name'. TextField")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.instance_next_button))).click()
            logger.info(f"Click on 'Next. Button")
            WebDriverWait(self.cpe_driver, 70).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.bsct_summary))).click()
            logger.info(f"Wait for 'Summary'. TextField")
            WebDriverWait(self.cpe_driver, 70).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.finish_button))).click()
            logger.info(f"Clicked 'Finish'. TextField")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.success_text))).is_displayed()
            logger.info(f"successfully created.")
            created_group_element = WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH,self.created_folder)))
            if created_group_element.is_displayed():
                logger.info(f"Instance folder got created")
                time.sleep(5)
                screenshot_path = self.highlighter.highlight_element(self.cpe_driver, created_group_element, testcase_name="instancewizard")
                print(f"Screenshot saved at: {screenshot_path}")    
                instancewizard = "PASSED"
            else:
                logger.error(f"Creation of instance folder failed.")                    
        except Exception as f:
                raise CPESanityTestException(f"Failed to creatioon of parent folder", cause=f) from f   
        finally:
            update_status("instancewizard", instancewizard, self.product)
            self.deletion_instancewizard()
            
    def deletion_documentclass(self):
        """
        Method name: deletion_instancewizard
        Author: Nadil Rudhainif (nadil.rudhainif@ibm.com)
        Description: This function is used to delete the created instance
        Parameters:
            None
        Returns
            None
        """ 
        try:
            wait = WebDriverWait(self.cpe_driver, 60)
            logger.info(f"Deleting the Document...")
            time.sleep(3)
            wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.document_doc_expand))).click()
            logger.info(f"Clicked on 'Document Expand' button")
            if wait.until(EC.visibility_of_element_located((By.XPATH, self.document))).is_displayed():
                wait.until(EC.visibility_of_element_located((By.XPATH, self.document))).click()
                logger.info(f"Clicked on 'Document' button")
                wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.document_doc_action_button))).click()
                logger.info(f"Clicked on 'Action' button") 
                wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.document_doc_delete_button))).click()
                logger.info(f"Clicked on 'Delete' button")
                wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.document_admin_text)))
                logger.info(f"Wait For 'Admin' Text")
                wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.ok_button))).click()
                logger.info(f"Clicked on 'OK' button")
                wait.until(EC.invisibility_of_element((By.XPATH, self.document)))
                logger.info(f"Document got deleted")
                wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.document_doc_expand))).click()
                logger.info(f"Document tab is minimized")
                time.sleep(2)
            wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.document_folder_expand))).click()
            logger.info(f"Clicked on 'Folder Expand' button")
            if wait.until(EC.visibility_of_element_located((By.XPATH, self.folder))).is_displayed():
                wait.until(EC.visibility_of_element_located((By.XPATH, self.folder))).click()
                logger.info(f"Clicked on 'Folder' button")
                wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.document_doc_action_button))).click()
                logger.info(f"Clicked on 'Action' button") 
                wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.document_doc_delete_button))).click()
                logger.info(f"Clicked on 'Delete' button")
                wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.document_admin_text)))
                logger.info(f"Wait For 'Admin' Text")
                wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.ok_button))).click()
                logger.info(f"Clicked on 'OK' button")
                wait.until(EC.invisibility_of_element((By.XPATH, self.folder)))
                logger.info(f"Folder got deleted")
                wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.document_folder_expand))).click()
                logger.info(f"Folder tab is minimized")
                wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.instance_classes_expand))).click()
                logger.info(f"Class tab is minimized")
                wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.instance_datadesign_expand))).click()
                logger.info(f"Data Design tab is minimized")                
        except Exception as e:
            logger.error(f"Error occurred while deleting folder: {str(e)}", exc_info=True)
            raise CPESanityTestException("Failed during Folder Wizard") from e   

    def create_document_class(self):
        """
        Method name: create_document_class
        Author: Nadil Rudhainif (nadil.rudhainif@ibm.com)
        Description: This function is used to verify whether able to create document using class
        Parameters:
            None
        Returns
            None
        """
        try:
            doccreation = "FAILED"
            logger.info(f"Starting with creation of document using class'.")
            self.check_browser_objectstore_page()
            self.doc_creation()
            created_doc_element = WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, self.doc_created)))
            if created_doc_element.is_displayed():
                logger.info(f"Document successfully got created")
                time.sleep(5)
                screenshot_path = self.highlighter.highlight_element(self.cpe_driver, created_doc_element, testcase_name="doccreation")
                print(f"Screenshot saved at: {screenshot_path}")  
                doccreation = "PASSED"
                update_status("doccreation", doccreation, self.product)
            else:
                logger.error(f"Creation of document failed.")
            time.sleep(5)
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.document_newdoc_close))).click()
            logger.info(f"Click on 'New Document Close'. Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.document_doc_close))).click()
            logger.info(f"Click on 'Document Close'. Button")    
        except Exception as f:
                raise CPESanityTestException(f"Failed to creatioon of document", cause=f) from f 
        try:
            if doccreation == "PASSED":
                foldercreation = "FAILED"
                WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.document_folder_button))).click()
                logger.info("Click on 'Folder Class' Button.")
                WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.document_general_tab)))
                logger.info(f"Wait for 'General'. Tab")
                WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.document_doc_action_button))).click()
                logger.info(f"Clicked on 'Action'. DropDown")
                WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.document_newclass_button))).click()
                logger.info(f"Clicked on 'NewClass'. DropDown")
                WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.document_displayname_textfield))).send_keys(self.folder_name)
                logger.info(f"Add on 'Display Name'. Textfield")
                WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.document_symbolicname_textfield))).click()
                logger.info(f"Click on 'Symbolic Text Field'. Button")
                WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.cpe_next_button))).click()
                logger.info(f"Click on 'Next. Button")
                WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.document_objectvalue_text)))
                logger.info(f"Wait for 'Object Value'. Text")
                WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.cpe_next_button))).click()
                logger.info(f"Click on 'Next. Button")
                WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.bsct_summary))).click()
                logger.info(f"Wait for 'Summary'. TextField")
                WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.finish_button))).click()
                logger.info(f"Clicked 'Finish'. TextField")
                WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.success_text)))
                logger.info(f"Wait For 'Success'. Text")
                WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.document_open_button))).click()
                logger.info(f"Click on 'Open'. Button")
                folderclass = WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, self.folder_created)))
                if folderclass.is_displayed():
                    logger.info(f"Folder successfully got created")
                    time.sleep(5)
                    screenshot_path = self.highlighter.highlight_element(self.cpe_driver, folderclass, testcase_name="foldercreation")
                    print(f"Screenshot saved at: {screenshot_path}")  
                    foldercreation = "PASSED"
                else:
                    logger.error(f"Creation of folder failed.")
                    foldercreation = "FAILED"
                time.sleep(5)
                WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.document_newfolder_close))).click()
                logger.info(f"Click on 'New Folder Close'. Button")
                WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.document_folder_close))).click()
                logger.info(f"Click on 'Folder Close'. Button")    
            else:
                logger.error(f"Folder creation failed. Aborting.")
        except Exception as g:
                raise CPESanityTestException(f"Failed to creatioon of folder", cause=g) from g   
        finally:
            
            update_status("foldercreation", foldercreation, self.product)
            if doccreation == "PASSED":
                try:
                    self.deletion_documentclass()
                except Exception as del_err:
                    logger.error("Error during deletion in finally block", exc_info=True)

    
    def deletion_markingset(self):
        """
        Method name: deletion_markingset
        Author: Nadil Rudhainif (nadil.rudhainif@ibm.com)
        Description: This function is used to delete the created marking set
        Parameters:
            None
        Returns
            None
        """ 
        try:
            wait = WebDriverWait(self.cpe_driver, 60)
            file = wait.until(EC.visibility_of_element_located((By.XPATH, self.created_markingset)))
            if file.is_displayed():
                logger.info("Deleting the subfolder class file...")
                wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.bsct_datadesign_close))).click()
                logger.info("Clicked on 'Data Design Close' button")
                wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.markingset_close_button))).click()
                logger.info("Clicked on 'Marking Set Close' button")
                wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.markingset_action_button))).click()
                logger.info("Clicked on 'Data Design Expand' button")
                wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.markingset_delete_button))).click()
                logger.info("Clicked on 'Delete' button")
                if WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.markingset_administration_text))).is_displayed():
                    WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.markingset_admin_ok_button))).click()
                logger.info(f"Clicked 'Admin OK'. Button")
                wait.until(EC.invisibility_of_element((By.XPATH, LocatorElements.markingset_admin_ok_button)))
                logger.info("Marking Set got deleted")

        except Exception as e:
                logger.error(f"Error occurred while deletion of marking set: {str(e)}", exc_info=True)
                raise CPESanityTestException("Failed during Marking set Deletion") from e
        
    def create_marking_set(self):
        """
        Method name: create_marking_set
        Author: Nadil Rudhainif (nadil.rudhainif@ibm.com)
        Description: This function is used to verify the marking set is getting created or not
        Parameters:
            None
        Returns
            None
        """
        try:
            markingset = "FAILED"
            logger.info(f"Starting with creation of marking set'.")
            self.check_browser_p8domain_page()
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.globalconfig_button))).click()
            logger.info(f"Clicked on 'Global Config'. Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.markingset_datadesign_button))).click()
            logger.info(f"Clicked on 'Data Design'. Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.markingset_button))).click()
            logger.info(f"Select 'Marking Set'. Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.markingset_new_create_button))).click()
            logger.info(f"Clicked on 'New'. Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.markingset_display_button))).send_keys(self.markingset_name)
            logger.info(f"Addon Display Name'. Field")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.markingset_description_textarea))).click()
            logger.info(f"Clicked on Description '. Text Field")
            checkbox = WebDriverWait(self.cpe_driver, 10).until(EC.presence_of_element_located((By.XPATH, LocatorElements.markingset_checkbox)))
            if not checkbox.is_selected():
                self.cpe_driver.execute_script("arguments[0].click();", checkbox)
                logger.info("Clicked Marking Set checkbox.")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.markingset_next_button))).click()
            logger.info(f"Clicked on 'Next'. Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.markingset_new_button))).click()
            logger.info(f"Clicked on 'New'. Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.markingset_value_text)))
            logger.info(f"Wait for 'Marking Value'. Text")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.markingset_markingvalue_textfield))).send_keys(self.markingvalue)
            logger.info(f"Add on 'Marking Value. Text Field")
            WebDriverWait(self.cpe_driver, 70).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.markingset_ok_button))).click()
            logger.info(f"Clicked for 'OK'. TextField")
            WebDriverWait(self.cpe_driver, 70).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.markingset_next_button))).click()
            logger.info(f"Clicked 'Next'. TextField")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.bsct_summary)))
            logger.info(f"Wait for 'Summary'. Text")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.finish_button))).click()
            logger.info(f"Clicked 'Finish'. TextField")
            if WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.markingset_administration_text))).is_displayed():
                WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.markingset_admin_ok_button))).click()
                logger.info(f"Clicked 'Admin OK'. Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.success_text)))
            logger.info(f"Wait For 'Success'. Text")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.markingset_open_button))).click()
            logger.info(f"successfully created.")
            element_marking_set = WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH,self.created_markingset)))
            if element_marking_set.is_displayed():
                logger.info(f"Marking set got created")
                time.sleep(5)
                screenshot_path = self.highlighter.highlight_element(self.cpe_driver, element_marking_set, testcase_name="markingset")
                print(f"Screenshot saved at: {screenshot_path}")    
                markingset = "PASSED"
            else:
                logger.error(f"Creation of Marking set failed.")                    
        except Exception as f:
                raise CPESanityTestException(f"Failed on the creation of marking set", cause=f) from f   
        finally:
            update_status("markingset", markingset, self.product)
            if markingset == "PASSED":
                try:
                    self.deletion_markingset()
                except Exception as del_err:
                    logger.error("Error during deletion in finally block", exc_info=True)

    def doc_creation(self):
        """
        Method name: doc_creation
        Author: Nadil Rudhainif (nadil.rudhainif@ibm.com)
        Description: This is a generalised function to create a document.
        Parameters:
            None
        Returns
            None
        """ 
        WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.instance_datadesign_expand))).click()
        logger.info(f"Clicked on 'Data Design Expand'. Button")
        WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.instance_classes_expand))).click()
        logger.info(f"Clicked on 'Classes Expand'. Button")
        WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.document_doc_button))).click()
        logger.info("Click on 'Document Class'.")
        WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.document_general_tab)))
        logger.info(f"Wait for 'General'. Tab")
        WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.document_doc_action_button))).click()
        logger.info(f"Clicked on 'Action'. DropDown")
        WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.document_newclass_button))).click()
        logger.info(f"Clicked on 'NewClass'. DropDown")
        WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.document_displayname_textfield))).send_keys(self.document_folder_name)
        logger.info(f"Add on 'Display Name'. Textfield")
        WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.document_symbolicname_textfield))).click()
        logger.info(f"Click on 'Symbolic Text Field'. Button")
        WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.cpe_next_button))).click()
        logger.info(f"Click on 'Next. Button")
        WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.document_objectvalue_text)))
        logger.info(f"Wait for 'Object Value'. Text")
        WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.cpe_next_button))).click()
        logger.info(f"Click on 'Next. Button")
        WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.bsct_summary))).click()
        logger.info(f"Wait for 'Summary'. TextField")
        WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.finish_button))).click()
        logger.info(f"Clicked 'Finish'. TextField")
        WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.success_text)))
        logger.info(f"Wait For 'Success'. Text")
        WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.document_open_button))).click()
        logger.info(f"Click on 'Open'. Button") 

    def deletion_subscription(self):
        """
        Method name: deletion_subscription
        Author: Nadil Rudhainif (nadil.rudhainif@ibm.com)
        Description: This function is used to delete the created subscription
        Parameters:
            None
        Returns
            None
        """ 
        try:
            wait = WebDriverWait(self.cpe_driver, 60)
            logger.info(f"Deleting the Subscription...")
            time.sleep(3)
            if wait.until(EC.visibility_of_element_located((By.XPATH, self.created_subscriptions))).is_displayed():
                wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.subscription_post_action_button))).click()
                logger.info(f"Clicked on 'Action' button") 
                wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.subscription_post_delete_button))).click()
                logger.info(f"Clicked on 'Delete' button")
                if wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.subscription_post_event_deletion_text))).is_displayed():
                    checkbox = WebDriverWait(self.cpe_driver, 10).until(EC.presence_of_element_located((By.XPATH, LocatorElements.subscription_event_deletion_checkbox)))
                    if not checkbox.is_selected():
                        self.cpe_driver.execute_script("arguments[0].click();", checkbox)
                        logger.info("Clicked Status checkbox.")
                    wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.markingset_ok_button))).click()
                    logger.info(f"Clicked on 'OK' button")
                wait.until(EC.invisibility_of_element((By.XPATH, LocatorElements.subscription_post_event_deletion_text)))
                logger.info("Subscription got deleted")
                wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.instance_classes_expand))).click()
                logger.info(f"Minimized 'Classes' Expand Field") 
                wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.instance_datadesign_expand))).click()
                logger.info(f"Minimized 'Data Design' Expand Field") 
                wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.subscription_docfile_close_button))).click()
                logger.info(f"Clicked on 'DOC Close' button")    
        except Exception as e:
            logger.error(f"Error occurred while deleting subscription: {str(e)}", exc_info=True)
            raise CPESanityTestException("Failed during Subscription deletion") from e   
        

    def create_subscription_wizard(self):
        """
        Method name: create_subscription_wizard
        Author: Nadil Rudhainif (nadil.rudhainif@ibm.com)
        Description: This function is used to verify whether able to create subscriptions or not
        Parameters:
            None
        Returns
            None
        """
        try:
            subcreation = "FAILED"
            logger.info(f"Starting with creation of document using class'.")
            self.check_browser_objectstore_page()
            self.doc_creation()
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.subscription_doc_close))).click()
            logger.info(f"Clicked on ' DOC Close'. Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.subscription_action_button))).click()
            logger.info(f"Clicked on 'Action'. Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.subscription_new_subscription))).click()
            logger.info(f"Clicked on 'New Subscription'. Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.subscription_displayname))).send_keys(self.subscription_name)
            logger.info(f"Added on 'Display Name'. Text Field")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.subscription_description))).click()
            logger.info(f"Clicked on 'Descrption'. Text Area")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.subscription_next_button))).click()
            logger.info(f"Clicked on 'Next'. Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.subscription_specify_text)))
            logger.info(f"Wait for 'Specifiy'. Text")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.subscription_next_button))).click()
            logger.info(f"Clicked on 'Next'. Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.subscription_deletion_checkbox))).click()
            logger.info(f"Clicked on 'Deletion'. CheckBox")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.subscription_update_even_checkbox))).click()
            logger.info(f"Clicked on 'Update Even'. Checkbox")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.subscription_next_button))).click()
            logger.info(f"Clicked on 'Next'. Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.subscription_event_new_button))).click()
            logger.info(f"Clicked on 'New'. Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.subscription_event_displayname))).send_keys(self.eventname)
            logger.info(f"Add on 'Event Name'. TextField")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.subscription_event_descriptionname))).click()
            logger.info(f"Clicked on 'Description'. Text Area")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.subscription_event_nextbutton))).click()
            logger.info(f"Clicked on 'Next'. Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.subscription_event_actiontype_text)))
            logger.info(f"Waited for 'Action Type'. Text")
            event_action_dropdown=WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.subscription_eventaction_dropdown)))
            event_action_dropdown.clear()
            event_action_dropdown.send_keys("Event Action")
            time.sleep(1)
            event_action_dropdown.send_keys(Keys.ENTER)
            time.sleep(1)
            logger.info(f"Added on 'Event Action'. Value")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.subscription_event_nextbutton))).click()
            logger.info(f"Clicked on 'Next'. Button")
            checkbox = WebDriverWait(self.cpe_driver, 10).until(EC.presence_of_element_located((By.XPATH, LocatorElements.processor_javascript_radiobutton)))
            if not checkbox.is_selected():
                self.cpe_driver.execute_script("arguments[0].click();", checkbox)
                logger.info("Clicked Status checkbox.")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.subscription_event_nextbutton))).click()
            logger.info(f"Clicked on 'Next'. Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.subscription_event_action_script_text)))
            logger.info(f"Wait for 'Event Action Script'. Text")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.subscription_event_nextbutton))).click()
            logger.info(f"Clicked on 'Next'. Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.bsct_summary)))
            logger.info(f"Wait for 'Summary'. Text")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.subscription_event_finish_button))).click()
            logger.info(f"Clicked on 'Finish'. Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.success_text)))
            logger.info(f"Wait for 'Success'. Text")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.subscription_event_close_button))).click()
            logger.info(f"Clicked on 'Close'. Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.subscription_event_action_text)))
            logger.info(f"Wait for 'Action Type'. Text")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.subscription_next_button))).click()
            logger.info(f"Clicked on 'Next'. Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.subscription_additionaloption_text)))
            logger.info(f"Wait for 'Additional Option'. Text")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.subscription_runmode_checkbox)))
            logger.info(f"Clicked on 'Run Mode'. Checkbox")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.subscription_next_button))).click()
            logger.info(f"Clicked on 'Next'. Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.bsct_summary)))
            logger.info(f"Wait for 'Summary'. Text")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.finish_button))).click()
            logger.info(f"Clicked 'Finish'. TextField")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.success_text)))
            logger.info(f"Wait for 'Success'. Text")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.subscription_open_button))).click()
            logger.info(f"Clicked 'Open'. TextField")
            time.sleep(5)
            element_subscription = WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH,self.created_subscriptions)))
            logger.info(element_subscription)
            time.sleep(5)
            if element_subscription.is_displayed():
                logger.info(f"Subscription got created")
                time.sleep(5)
                created_path = self.highlighter.highlight_element(self.cpe_driver, element_subscription, testcase_name="subcreation")
                print(f"Screenshot saved at: {created_path}")    
                subcreation = "PASSED"  
            else:
                logger.error(f"Subscription creation failed.")                 
        except Exception as f:
                raise CPESanityTestException(f"Failed to create subscription", cause=f) from f   
        finally:
            update_status("subcreation", subcreation, self.product)
            if subcreation == "PASSED":
                try:
                    self.deletion_subscription()
                except Exception as del_err:
                    logger.error("Error during deletion in finally block", exc_info=True) 


    def deletion_document_life_cycle_action_wizard(self):
        """
        Method name: deletion_subscription
        Author: Nadil Rudhainif (nadil.rudhainif@ibm.com)
        Description: This function is used to delete the created subscription
        Parameters:
            None
        Returns
            None
        """ 
        try:
            wait = WebDriverWait(self.cpe_driver, 60)
            logger.info(f"Deleting the Created life cycle action wizard..")
            time.sleep(3)
            if wait.until(EC.visibility_of_element_located((By.XPATH, self.created_life_cycle_action))).is_displayed():
                wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.lifecycle_action_button))).click()
                logger.info(f"Clicked on 'Action' button") 
                wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.lifecycle_delete_button))).click()
                logger.info(f"Clicked on 'Delete' button")
                if wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.document_admin_text))).is_displayed():
                    wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.lifecycle_ok_button))).click()
                    logger.info(f"Clicked on 'OK' button")
                wait.until(EC.invisibility_of_element((By.XPATH, LocatorElements.document_admin_text)))
                logger.info(f"Document file got deleted.")
                wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.subscription_doc_close))).click()
                logger.info(f"Clicked on 'Close' Button") 
                WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.lifecycle_event_action_expand))).click()
                logger.info(f"Clicked on 'Event Action Expand'. Button")
  
        except Exception as e:
            logger.error(f"Error occurred while deleting document life cycle: {str(e)}", exc_info=True)
            raise CPESanityTestException("Failed during document life cycle deletion") from e   
        

    def create_document_life_cycle_action_wizard(self):
        """
        Method name: create_document_life_cycle_action_wizard
        Author: Nadil Rudhainif (nadil.rudhainif@ibm.com)
        Description: This function is used to verify whether able to create a document life cycle action wizard using java script
        Parameters:
            None
        Returns
            None
        """
        try:
            lifecycle = "FAILED"
            logger.info(f"Starting with creation of document life cycle action wizard using javascript'.")
            self.check_browser_objectstore_page()
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.lifecycle_event_action_expand))).click()
            logger.info(f"Clicked on ' Event Action Expand'. Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.element_to_be_clickable((By.XPATH, LocatorElements.lifecycle_defect_life_cycle_action_button))).click()
            logger.info(f"Clicked on 'Action'. Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.lifecycle_new_button))).click()
            logger.info(f"Clicked on 'New'. Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.lifecyle_display_textfield))).send_keys(self.life_cyle_action_name)
            logger.info(f"Added on 'Display Name'. Text Field")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.lifecycle_description_textarea))).click()
            logger.info(f"Clicked on 'Description'. Text Area")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.lifecycle_next_button))).click()
            logger.info(f"Clicked on 'Next'. Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.lifecycle_specify_documentation_text)))
            logger.info(f"Wait for 'Specifiy'. Text")
            try:
                next_button = WebDriverWait(self.cpe_driver, 10).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.lifecycle_next_button)))
                if next_button.is_displayed():
                    next_button.click()
                    logger.info("Clicked on 'Next' button.")
            except TimeoutException:
                 logger.warning("The 'Next' button was not visible within the timeout period. Continuing with the rest of the script.")

            checkbox = WebDriverWait(self.cpe_driver, 10).until(EC.presence_of_element_located((By.XPATH, LocatorElements.processor_javascript_radiobutton)))
            if not checkbox.is_selected():
                self.cpe_driver.execute_script("arguments[0].click();", checkbox)
                logger.info("Clicked Status checkbox.")
            
            try:
                java_handler_elem = WebDriverWait(self.cpe_driver, 10).until(EC.presence_of_element_located((By.XPATH, LocatorElements.lifecycle_java_handler_text)))
                if java_handler_elem.is_displayed():
                    logger.info("Waited for 'JAVA Handler' alert.")       
                    ok_button = WebDriverWait(self.cpe_driver, 10).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.ok_button)))
                    if ok_button.is_displayed():
                        ok_button.click()
                        logger.info("Clicked on 'OK' button.")
                else:
                    logger.info("'JAVA Handler' alert is not visible. Continuing execution.")
            except TimeoutException:
                logger.info("'JAVA Handler' alert not found within timeout. Skipping.")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.lifecycle_next_button))).click()
            logger.info(f"Clicked on 'Next'. Button")
            try:
                event_script_text = WebDriverWait(self.cpe_driver, 10).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.lifecycle_enter_the_doc_text)))
                if event_script_text.is_displayed():
                    logger.info("Found 'Event Action Script' text.")
                    try:
                        next_button = WebDriverWait(self.cpe_driver, 10).until(EC.element_to_be_clickable((By.XPATH, LocatorElements.lifecycle_next_button)))
                        if next_button.is_displayed():
                            next_button.click()
                            logger.info("Clicked on 'Next' button after 'Event Action Script'.")
                    except TimeoutException:
                        logger.warning("The 'Next' button was not visible within the timeout period after 'Event Action Script'. Skipping.")
            except TimeoutException:
                logger.warning("The 'Event Action Script' text was not visible within the timeout period. Skipping.")

            try:
                object_properties_elem = WebDriverWait(self.cpe_driver, 10).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.processor_objectproperties_text)))
                if object_properties_elem.is_displayed():
                    object_properties_elem.click()
                    logger.info("Clicked on 'Object Properties' text.")
                    next_button = WebDriverWait(self.cpe_driver, 10).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.lifecycle_next_button)))
                    if next_button.is_displayed():
                        next_button.click()
                        logger.info("Clicked on 'Next' button.")
            except TimeoutException:
                logger.warning("'Object Properties' text was not visible within the timeout period. Continuing.")

            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.bsct_summary)))
            logger.info(f"Wait for 'Summary'. Text")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.lifecycle_finish_button))).click()
            logger.info(f"Clicked on 'Finish'. Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.success_text)))
            logger.info(f"Wait for 'Success'. Text")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.lifecycle_open_button))).click()
            logger.info(f"Clicked on 'Open'. Button")
            time.sleep(5)
            element_lifecycle = WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH,self.created_life_cycle_action)))
            logger.info(element_lifecycle)
            time.sleep(5)
            if element_lifecycle.is_displayed():
                logger.info(f"Document life cycle action wizard got created using java script")
                time.sleep(5)
                created_path = self.highlighter.highlight_element(self.cpe_driver, element_lifecycle, testcase_name="lifecycle")
                print(f"Screenshot saved at: {created_path}")    
                lifecycle = "PASSED"  
            else:
                logger.error(f"Document life cycle creation failed.")                 
        except Exception as f:
                raise CPESanityTestException(f"Failed to create document life cycle", cause=f) from f   
        finally:
            update_status("lifecycle", lifecycle, self.product)
            if lifecycle == "PASSED":
                try:
                    self.deletion_document_life_cycle_action_wizard()
                except Exception as del_err:
                    logger.error("Error during deletion in finally block", exc_info=True)    
           
        
    def create_property_template(self):
        """
        Method name: create_property_template
        Author: Nadil Rudhainif (nadil.rudhainif@ibm.com)
        Description: This function is used to verify whether we are able to create property template.
        Parameters:
            None
        Returns
            None
        """
        self.wait = WebDriverWait(self.cpe_driver, 60)
        propertytemplateobject = "FAILED"
        try:
            self.check_browser_objectstore_page()
            self.wait.until(EC.element_to_be_clickable((By.XPATH, LocatorElements.data_design))).click()
            logger.info("Clicked on 'Data Design' folder.")
            logger.info("Waiting for the 'Property Templates' link to be clickable")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, LocatorElements.property_templates))).click()
            logger.info("Clicked on 'Property Templates' link.")
            logger.info("Waiting for the 'New' button to be clickable")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, LocatorElements.new_prop_temp))).click()
            logger.info("Clicked on 'New' button.")

            logger.info("Waiting for the 'Display Name' field to be clickable")
            display_name = self.wait.until(EC.element_to_be_clickable((By.XPATH, LocatorElements.property_template_display_name)))
            display_name.click()
            logger.info("Clicked on 'Display Name' field.")
            display_name.clear()
            display_name.send_keys(self.property_template_name)

            logger.info("Waiting for the 'Description' field to be clickable")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, LocatorElements.property_template_description))).click()

            logger.info("Waiting for the 'Next' button to be clickable")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, LocatorElements.property_template_next_button))).click()
            logger.info("Clicked on 'Next' button.")

            logger.info("Waiting for the 'Select the Data type' element to be visible")
            data_type = self.wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.select_data_type)))

            logger.info("Waiting for the 'Data type' dropdown to be present")
            data_type_drop_down=self.wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.property_template_data_type_drop)))
            data_type_drop_down.clear()
            data_type_drop_down.send_keys("Object")
            time.sleep(2)
            data_type_drop_down.send_keys(Keys.ENTER)
            logger.info("Selected 'Object' Datatype.")
            time.sleep(1)
            logger.info("Waiting for the 'Next' button to be clickable")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, LocatorElements.property_template_next_button))).click()
            logger.info("Clicked on 'Next' button.")

            logger.info("Waiting for the 'Select Single or Multi Value Text' element to be visible")
            self.wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.property_template_single_multi_text)))

            logger.info("Waiting for the 'Next' button to be clickable")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, LocatorElements.property_template_next_button))).click()
            logger.info("Clicked on 'Next' button.")

            self.wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.bsct_summary)))
            logger.info(f"Wait for 'Summary'. Text")
            logger.info("Waiting for the 'Finish' button to be clickable")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, LocatorElements.property_template_finish_button))).click()
            logger.info("Clicked on 'Finish' button.")

            logger.info("Waiting for the 'Success' label to be visible")
            self.wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.create_success)))

            logger.info("Waiting for the 'Open' button to be clickable")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, LocatorElements.property_template_open_button))).click()
            logger.info("Clicked on 'Open' button.")
            time.sleep(3)
            logger.info(self.created_propertytemplate)
            element_prop = WebDriverWait(self.cpe_driver, 80).until(EC.visibility_of_element_located((By.XPATH,self.created_propertytemplate)))
            if element_prop.is_displayed():
                time.sleep(5)
                created_property_template = self.highlighter.highlight_element(self.cpe_driver, element_prop, testcase_name="propertytemplateobject")
                propertytemplateobject = "PASSED"
                logger.info("Waiting for the 'Close' button to be clickable")
                self.wait.until(EC.element_to_be_clickable((By.XPATH, LocatorElements.property_template_close_button))).click()
                logger.info("Clicked on 'Close' button.")
            else:
                logger.error("Failed to create the property template")
  
        except Exception as e:
            propertytemplateobject = "FAILED"
            raise Exception(f"Failed to create property template:: {e}.")

        finally:
            update_status("propertytemplateobject", propertytemplateobject, self.product)
            if propertytemplateobject == "PASSED":
                try:
                    self.adding_property_template()
                except Exception as del_err:
                     logger.error("Error during while adding the property template in property definition", exc_info=True) 
        

    def adding_property_template(self):
        """
        Method name: adding_property_template
        Author: Nadil Rudhainif (nadil.rudhainif@ibm.com)
        Description: This function is used to verify that adding property template in property definition
        Parameters:
            None
        Returns
            None
        """
        try:
            addingprop = "FAILED"
            logger.info(f"Starting with adding property template in property definition'.")
            WebDriverWait(self.cpe_driver, 60).until(EC.element_to_be_clickable((By.XPATH, LocatorElements.property_template_prop_close))).click()
            logger.info("Clicked on 'Property Close' button.")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.instance_classes))).click()
            logger.info(f"Clicked on ' Classes'. Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.document_class))).click()
            logger.info(f"Clicked on 'Document'. Link")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.property_template_property_definition_tab))).click()
            logger.info(f"Clicked on 'Property Definition'. Button")
           
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.property_template_add_button))).click()
            logger.info(f"Clicked on 'Add' Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.property_template_propertydefinition_searchtab))).send_keys(self.property_template_name)
            logger.info(f"Search for 'created property'.")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.property_template_filter_button))).click()
            logger.info(f"Clicked on 'Filter'. Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, self.search_propertytemplate))).click()
            logger.info(f"Clicked on 'Property Template'. List")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.markingset_ok_button))).click()
            logger.info(f"Clicked on 'Ok'. Button")
            created_property = WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, self.created_propertytemplate_link)))
            created_property.click()
            logger.info(f"Clicked on 'Property Template'. Link")
            element_added_prop=WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, self.added_property_template)))
            if element_added_prop.is_displayed():
                logger.info(f"Adding property template in property definition is successfully completed ")
                created_path = self.highlighter.highlight_element(self.cpe_driver, element_added_prop, testcase_name="addingprop")
                print(f"Screenshot saved at: {created_path}")    
                addingprop = "PASSED"  
            else:
                logger.error(f"Failed to add property template in property definition.") 
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.property_template_more_button))).click()
            logger.info(f"Clicked on 'More'. Button")
            required_class=WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.property_template_requiredclass_field)))
            required_class.send_keys("Class Definition")
            required_class.send_keys(Keys.ENTER)
            logger.info(f"Added 'Required Class'. Text Field")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.property_template_view_properites_dropdown)))
            logger.info(f"Waited for 'Properties'. Session")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.property_template_savebutton))).click()
            logger.info(f"Clicked on 'Save'. Button")
            element_invisible = WebDriverWait(self.cpe_driver, 60).until(EC.invisibility_of_element((By.XPATH, LocatorElements.property_template_savebutton)))
            logger.info(f"Wait for the file to be 'Saved'.")
            if element_invisible:
                logger.info("The file was saved successfully,")
            else:
                logger.error("Save did NOT succeed element is still visible.")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.property_template_close_doc))).click()
            logger.info(f"Clicked on 'Doc Close'. Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.property_template_classes_close_button))).click()
            logger.info(f"Clicked on 'Class Close'. Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.bsct_datadesign_close))).click()
            logger.info(f"Clicked on 'Data Design Close'. Button")
                             
        except Exception as f:
                raise CPESanityTestException(f"Failed to add the property template", cause=f) from f   

        finally:
            update_status("addingprop", addingprop, self.product)


    def create_custom_object_wizard(self):
        """
        Method name: create_custom_object_wizard
        Author: Nadil Rudhainif (nadil.rudhainif@ibm.com)
        Description: This function is used to verify the creation of custom object wizard
        Parameters:
            None
        Returns
            None
        """
        try:
            customobject = "FAILED"
            logger.info(f"Starting with creation of custom object.")
            self.check_browser_objectstore_page()
            self.check_and_create_security_policy()

            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.instance_browser_expand))).click()
            logger.info(f"Clicked on 'Browser Expand'. Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.rootfolder))).click()
            logger.info(f"Clicked on 'Root Folder'. Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.custom_object_actions_button))).click()
            logger.info(f"Clicked on 'Action'. Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.custom_object_new))).click()
            logger.info(f"Clicked on 'New Custom Object'. Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.custom_object_containment_name_textfield))).send_keys(self.containment_name)
            logger.info(f"Added to the 'Containment Name'. Field")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.custom_object_next_button))).click()
            logger.info(f"Clicked on 'Next'. Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.subfolder_object_properties)))
            logger.info(f"Waited for 'Object Properties'. Text")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.custom_object_next_button))).click()
            logger.info(f"Clicked on 'Next'. Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.custom_object_retaining_option_text)))
            logger.info(f"Waited for 'Custom Retaining Option'. Text")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.custom_object_next_button))).click()
            logger.info(f"Clicked on 'Next'. Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.bsct_summary)))
            logger.info("Summary data is available.")
            WebDriverWait(self.cpe_driver, 60).until(EC.element_to_be_clickable((By.XPATH, LocatorElements.finish_button))).click()
            logger.info("Clicked 'Finish' button.")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.success_text)))
            logger.info("Success message appeared.")
            WebDriverWait(self.cpe_driver, 60).until(EC.element_to_be_clickable((By.XPATH, LocatorElements.subfolder_open_button))).click()
            logger.info("Clicked on 'Open' button.")
            element_custom = WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, self.created_custom_object)))
            if element_custom.is_displayed():
                logger.info(f"Creating custom object wizard is successfull ")
                time.sleep(2)
                created_path = self.highlighter.highlight_element(self.cpe_driver, element_custom, testcase_name="customobject")
                print(f"Screenshot saved at: {created_path}")    
                customobject = "PASSED" 
            else:
                logger.error(f"Failed to create custom object wizard is failed.") 
                           
        except Exception as f:
                raise CPESanityTestException(f"Failed to create custom object wizard", cause=f) from f   
        finally:
            update_status("customobject", customobject, self.product)
            if customobject == "PASSED":
                try:
                    self.adding_security_policy()
                except Exception as del_err:
                    logger.error("Error during adding the security policy to the custom object", exc_info=True)    

    def adding_security_policy(self):
        """
        Method name: adding_security_policy
        Author: Nadil Rudhainif (nadil.rudhainif@ibm.com)
        Description: This function is used to verify that adding security policy to the custom object
        Parameters:
            None
        Returns
            None
        """
        try:
            addsecurity = "FAILED"
            logger.info(f"Starting with adding security policy to the custom object'.")
            WebDriverWait(self.cpe_driver, 60).until(EC.element_to_be_clickable((By.XPATH, LocatorElements.security_policy_tab))).click()
            logger.info("Clicked on 'Security Policy Tab' button.")
            security_input_field= WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.security_policy_add_name)))
            security_input_field.clear()
            security_input_field.send_keys("TestSecurityPolicy")
            security_input_field.send_keys(Keys.ENTER)
            logger.info(f"Added the ' Security Policy Name'. Text Field")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.security_policy_released_radiobutton))).click()
            logger.info(f"Clicked on 'Radio'. Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.security_policy_save_button))).click()
            logger.info(f"Clicked on 'Save'. Button")
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.security_policy_save_verification)))
            logger.info(f"Waited for security Policy to be saved")
            element_created = WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.security_policy_created)))
            if element_created.is_displayed():
                logger.info(f"Security policy is added successfully")
                time.sleep(2)
                created_path = self.highlighter.highlight_element(self.cpe_driver, element_created, testcase_name="addsecurity")
                print(f"Screenshot saved at: {created_path}")    
                addsecurity = "PASSED"
                WebDriverWait(self.cpe_driver, 60).until(EC.element_to_be_clickable((By.XPATH, LocatorElements.custom_object_close_button))).click()
                logger.info("Clicked on 'Close' button.") 
            else:
                logger.error(f"Failed to save the create secuirty policy")  

            WebDriverWait(self.cpe_driver, 60).until(EC.element_to_be_clickable((By.XPATH, LocatorElements.subfolder_close_root_folder))).click()
            logger.info("Clicked on 'Root Folder Close' button.") 
            WebDriverWait(self.cpe_driver, 60).until(EC.visibility_of_element_located((By.XPATH, LocatorElements.instance_browser_expand))).click()
            logger.info(f"Clicked on 'Browser Expand To Minimize it'. Button")

        except Exception as f:
                raise CPESanityTestException(f"Failed to add the security policy", cause=f) from f   

        finally:
            update_status("addsecurity", addsecurity, self.product)


    def create_property_templates(self):
        """
        Method name: create_property_templates
        Author: Nadil Rudhainif
        Method Description: This method creates a new property template
        Parameters:  None
        Returns: None
        """ 
        self.wait = WebDriverWait(self.cpe_driver, 60)
        propertytemplates = "FAILED"
        try:
            self.check_browser_objectstore_page()
            logger.info("Waiting for the 'Data Design' folder to be clickable")
            self.wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.data_design))).click()
            logger.info("Clicked on 'Data Design' folder.")
            logger.info("Waiting for the 'Property Templates' link to be clickable")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, LocatorElements.property_templates))).click()
            logger.info("Clicked on 'Property Templates' link.")
            logger.info("Waiting for the 'New' button to be clickable")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, LocatorElements.new_prop_temp))).click()
            logger.info("Clicked on 'New' button.")

            logger.info("Waiting for the 'Display Name' field to be clickable")
            display_name = self.wait.until(EC.element_to_be_clickable((By.XPATH, LocatorElements.property_template_display_name)))
            display_name.click()
            logger.info("Clicked on 'Display Name' field.")
            display_name.clear()
            display_name.send_keys(self.property_templates_name)

            self.wait.until(EC.element_to_be_clickable((By.XPATH, LocatorElements.property_template_description))).click()
            self.wait.until(EC.element_to_be_clickable((By.XPATH, LocatorElements.property_template_next_button))).click()
            logger.info("Clicked on 'Next' button.")
            logger.info("Waiting for the 'Select the Data type' element to be visible")
            data_type = self.wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.select_data_type)))
            time.sleep(1)
            logger.info("Waiting for the 'String' data type to be visible")
            data_type_drop_down=self.wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.property_template_data_type_drop)))
            data_type_drop_down.clear()
            data_type_drop_down.send_keys("String")
            time.sleep(2)
            data_type_drop_down.send_keys(Keys.ENTER)
            logger.info("Selected 'String' Datatype.")
            time.sleep(1)
            logger.info("Waiting for the 'Next' button to be clickable")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, LocatorElements.property_template_next_button))).click()
            logger.info("Clicked on 'Next' button.")
            logger.info("Waiting for the 'Select the Marketing type' element to be visible")
            self.wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.select_marketing_type)))
            self.wait.until(EC.element_to_be_clickable((By.XPATH, LocatorElements.subscription_event_new_button))).click()
            logger.info("Clicked on 'New' button.")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, LocatorElements.choice_display_name_textfield))).send_keys(self.choice_list_data)
            logger.info("Added 'ChoiceList' Value.")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, LocatorElements.choice_next_button))).click()
            logger.info("Clicked on 'Next' button.")

            self.wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.choice_select_text)))
            logger.info(f"Waiting for 'Select'. Text")
            self.wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.choice_next_button))).click()
            logger.info(f"Clicked 'Next'. TextField")
            self.wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.choice_new_group))).click()
            logger.info(f"Clicked on 'New Group'.Button")
            self.wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.choice_new_display_name))).send_keys(self.group_name)
            logger.info(f"Add 'GroupName'. TextField")
            self.wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.choice_add_button))).click()
            logger.info(f"Clicked on Add'.Button")
            self.wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.choice_ok_button))).click()
            logger.info(f"Clicked 'Ok'. Button")
            self.wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.choice_new_item))).click()
            logger.info(f"Clicked 'New Item'. Button")
            self.wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.choice_new_display_name))).send_keys(self.item_name)
            logger.info(f"Add 'GroupName'. TextField")
            self.wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.choice_add_button))).click()
            logger.info(f"Clicked on Add'.Button")
            self.wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.choice_ok_button))).click()
            logger.info(f"Clicked 'Ok'. Button")
            self.wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.choice_next_button))).click()
            logger.info(f"Clicked 'Next'. TextField")
            self.wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.bsct_summary))).click()
            logger.info(f"Wait for 'Summary'. TextField")
            self.wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.choice_list_finish_button))).click()
            logger.info(f"Clicked 'Finish'. TextField")
            self.wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.choice_list_created_close))).click()
            checkbox = self.wait.until(EC.presence_of_element_located((By.XPATH, LocatorElements.choice_list_assignchoice_checkbox)))
            if not checkbox.is_selected():
                self.cpe_driver.execute_script("arguments[0].click();", checkbox)
                logger.info("Clicked Assign Choice List checkbox.")

            logger.info("Waiting for the 'Next' button to be clickable")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, LocatorElements.property_template_next_button))).click()
            logger.info("Clicked on 'Next' button.")
            logger.info("Waiting for the 'Set other attributes' label to be visible")
            self.wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.other_attributes_label)))
            logger.info("Waiting for the 'Set Attributes' checklist to be clickable")
            self.wait.until(EC.presence_of_element_located((By.XPATH, LocatorElements.other_attributes))).click()
            logger.info("Clicked on 'Set Attributes' checklist.")
            logger.info("Waiting for the 'Next' button to be clickable")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, LocatorElements.property_template_next_button))).click()
            logger.info("Clicked on 'Next' button.")
            logger.info("Waiting for the 'Additional Property template Attributes' element to be visible")
            self.wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.additional_property_template)))
            logger.info("Waiting for the 'Next' button to be clickable")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, LocatorElements.property_template_next_button))).click()
            logger.info("Clicked on 'Next' button.")
            logger.info("Waiting for the 'Access Rights' element to be visible")
            self.wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.access_rights)))
            self.wait.until(EC.element_to_be_clickable((By.XPATH, LocatorElements.choice_list_selectall))).click()
            logger.info("Clicked on 'Select All' button.")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, LocatorElements.property_template_next_button))).click()
            logger.info("Clicked on 'Next' button.")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, LocatorElements.property_template_finish_button))).click()
            logger.info("Clicked on 'Finish' button.")
            logger.info("Waiting for the 'Success' label to be visible")
            self.wait.until(EC.visibility_of_element_located((By.XPATH, LocatorElements.create_success)))
            self.wait.until(EC.element_to_be_clickable((By.XPATH, LocatorElements.property_template_open_button))).click()
            logger.info("Clicked on 'Open' button.")
            time.sleep(5)
            element_property = WebDriverWait(self.cpe_driver, 80).until(EC.visibility_of_element_located((By.XPATH,self.created_propertytemplates)))
            if element_property.is_displayed():
                time.sleep(3)
                created_property_template = self.highlighter.highlight_element(self.cpe_driver, element_property, testcase_name="propertytemplates")
                propertytemplates = "PASSED"
                logger.info("Waiting for the 'Close' button to be clickable")
                self.wait.until(EC.element_to_be_clickable((By.XPATH, LocatorElements.property_template_close_button))).click()
                logger.info("Clicked on 'Close' button.")
                self.wait.until(EC.element_to_be_clickable((By.XPATH, LocatorElements.property_template_prop_close))).click()
                logger.info("Clicked on 'Property Close' button.")
                self.wait.until(EC.element_to_be_clickable((By.XPATH, LocatorElements.bsct_datadesign_close))).click()
                logger.info("Clicked on 'Data Design Close' button.")
            else:
                logger.error("Failed to create the property templates")
        
        except Exception as f:
                raise CPESanityTestException(f"Failed to create property templates", cause=f) from f   
        finally:
            update_status("propertytemplates", propertytemplates, self.product)



    def cpe_runner(self):
        """
        Method name: cpe_runner
        Author: Nadil Rudhainif (nadil.rudhainif@ibm.com)
        Description: This function acts as a runner file to execute the scripts
        Parameters:
            None
        Returns
            None
        """
        test_steps = [

            ("create_affinity_group", "create_affinity_group"),
            ("change_preprocessor_action", "change_preprocessor_action"),
            ("create_instance_wizard", "create_instance_wizard"),
            ("create_background_search_class_template", "create_background_search_class_template"),
            ("create_sub_folder", "create_sub_folder"),
            ("choice_list_wizard", "choice_list_wizard"),
            ("create_document_class", "create_document_class"),
            ("create_property_templates", "create_property_templates"),
            ("create_marking_set", "create_marking_set"),
            ("create_subscription_wizard", "create_subscription_wizard"),
            ("create_document_life_cycle_action_wizard", "create_document_life_cycle_action_wizard"),
            ("create_property_template", "create_property_template"),
            ("create_custom_object_wizard", "create_custom_object_wizard"),
            
        ]
        cpe_sanity = CPE()
        #reset execution data before starting the execution of testcases.
        self.reset_execution_data.reset_execution_data(CONFIG_FILE)
        for step_name, method_name in test_steps:
            logger.info(f"Starting test: {step_name}")
            try:
                method = getattr(cpe_sanity, method_name)
                method()
            except Exception as e:
                logger.error(f"{step_name} failed: {e}", exc_info=True)
                # Close the browser if failed
                cpe_sanity.safe_quit_driver()
                logger.info("Reinitializing browser for next test...")
                # Reinitializing the browser
                if not cpe_sanity.safe_reinitialize_browser():
                    logger.error("Aborting further tests: browser could not be recovered.")
                    break 
            else:
                logger.info(f"{step_name} completed successfully.")
        # Generate report
        try:
            cpe_sanity.create_report()
        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
        finally:
            cpe_sanity.safe_quit_driver()


    def safe_reinitialize_browser(self):
        """
        Method name: safe_reinitialize_browser
        Author: Nadil Rudhainif (nadil.rudhainif@ibm.com)
        Description: This function is used to re-initialize the browser
        Parameters:
            None
        Returns
            boolean
        """
        try:
            self.cpe = CpeAdmin() 
            self.cpe_driver = self.cpe.login(self.username, self.password)
            self.cpe_driver.timeouts.implicit_wait = 180
            self.actions = ActionChains(self.cpe_driver)
            logger.info("Browser reinitialized successfully.")
            return True
        except Exception as e:
            logger.error(f"Could not reinitialize browser: {e}")
            return False
        
    def safe_quit_driver(self):
        """
        Method name: safe_quit_driver
        Author: Nadil Rudhainif (nadil.rudhainif@ibm.com)
        Description: This function is quit the browser if failed
        Parameters:
            None
        Returns
            None
        """
        try:
            if hasattr(self, "cpe_driver") and self.cpe_driver:
                self.cpe_driver.quit()
                self.cpe_driver = None
                logger.info("Browser session closed successfully.")
        except Exception as e:
            logger.warning(f"Failed to close browser: {e}")

    def create_report(self):
        """
        Method name: create_report
        Author: Nadil Rudhainif (nadil.rudhainif@ibm.com)
        Description: This function is used to create or generate the report
        Parameters:
            None
        Returns
            None
        """
        try:
            generate_report.generate_html_report()
            pdf_report.convert_html_to_pdf(self.args.product.lower(), CONFIG_FILE)
        except Exception as e:
            logger.error(f"Failed to generate or convert report: {e}")

if __name__ == "__main__":
    cpe_sanity = CPE()
    cpe_sanity.cpe_runner()
