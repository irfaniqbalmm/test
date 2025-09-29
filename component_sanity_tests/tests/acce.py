import time
import os
import re
import sys

from tomlkit import parse
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from component_pages.cpe.cpe import CpeAdmin
from component_pages.utilities import scroll_element
from component_sanity_tests.exceptions.iccsap_exception import ICCSAPSanityTestException
from component_sanity_tests.exceptions.ier_exception import IERSanityTestException
from component_sanity_tests.utils.common_utils.browser_manager import BrowserManager
from component_sanity_tests.utils.common_utils.highlighter import highlighter
from utils.logger import logger
from utils.bvt_status import update_status
import inputs.locators as locators

class ACCE:

    def __init__(self, args) -> None:
        """
        Method name: __init__
        Description: Initializes the WebDriver with specified options and settings and fetching namespace, cluster from config file
        Parameters:
            args: arguments passed from command line(object stores)
        Returns:
            None
        """

        self.args = args
        config_file = self.args.config_file_path
        self.product = self.args.product.upper()

        with open(config_file, "r") as file :
            config = parse(file.read())

        self.namespace = config['configurations']['project_name']
        self.cluster = config['configurations']['cluster']

        self.username= config['credentials']['app_login_username']
        self.password = config['credentials']['app_login_password']

        self.screenshot_path = config[self.product.lower()]['screenshot_path']
        self.highlighter = highlighter(screenshot_dir=self.screenshot_path)

    def login_and_navigate_to_os(self):
        """
        Method name: login_and_navigate_to_os
        Authors: Anisha Suresh, Nusaiba K K 
        Method Description: Fucntion creates an instance of CpeAdmin and calls functions to login and navigate to Object Stores page.
        Parameters: None
        Returns: None
        Raises:
            ICCSAPSanityTestException: If an exception occurs while logging into ACCE and navigating to the Object Stores page for ICCSAP.
            IERSanityTestException: If an exception occurs while logging into ACCE and navigating to the Object Stores page for IER.
        """
        try:
            logger.info("Logging into ACCE and navigating to Object Stores Page")
            if not self.args.objectstore:
                logger.error("No objectstore name provided.")
                logger.critical(f"Exiting {self.product} Sanity tests!")
                sys.exit(1)

            self.cpe = CpeAdmin()
            self.cpe_driver = self.cpe.login(self.username, self.password)
            self.wait = WebDriverWait(self.cpe_driver, 180)
            self.cpe.navigate_to_object_store()

        except Exception as e:
            if self.product == "ICCSAP":
                raise ICCSAPSanityTestException("Failed while trying to login to ACCE and navigate to OS", cause=e) from e
            elif self.product == "IER":
                raise IERSanityTestException("Failed while trying to login to ACCE and navigate to OS", cause=e) from e


    def create_object_store_form(self, objectstore):
        """
        Method name: create_object_store_form
        Authors: Anisha Suresh, Nusaiba K K
        Create object stores as provided by the input parameter.
        Parameters:
            objectstore (str): Object store name to be created.
        Returns: None
        """
        def click_if_enabled(xpath):
            """
            Method name: click_if_enabled
            Author: Nusaiba K K
            Check if the element is enabled and click it.
            Parameters:
                xpath (str): Xpath of the element to be clicked.
            Returns: None
            """
            checkbox = self.wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
            is_disabled = checkbox.get_attribute("aria-disabled") == "true"
            if not is_disabled:
                self.wait.until(EC.element_to_be_clickable((By.XPATH, xpath))).click()
                logger.info(f"Clicked checkbox at {xpath}.")
            else:
                logger.info(f"Checkbox at {xpath} is disabled and cannot be clicked.")

        def fill_input(xpath, value, clear_first=False):
            """
            Method name: fill_input
            Author: Nusaiba K K
            Complete the object store creation form.
            Parameters:
                xpath (str): Xpath of the element to be clicked.
                value (str): Value to be filled in the field.
                clear_first (bool): Whether to clear the field before sending keys. Default is False.
            Returns: None
            """
            field = self.wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            if clear_first:
                field.clear()
            field.send_keys(value)

        object_store_creation = "FAILED"
        try:
            self.wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.new_object_store))).click()
            logger.info("Clicked on New object store button.")

            objectstorename = objectstore
            schemaname = f"{objectstorename}_Schema"
            logger.info(f"Creating Object Store: {objectstorename} with Schema: {schemaname}")
            time.sleep(5)
            fill_input(locators.LocatorElements.object_store_display_name, objectstorename)
            element = self.wait.until(EC.presence_of_element_located((By.XPATH, locators.LocatorElements.object_store_symbolic_name)))
            self.cpe_driver.execute_script("arguments[0].click();", element)
            logger.info("Provided object store symbolic name")

            self.wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.next_button))).click()

            fill_input(locators.LocatorElements.connection, "objectstore1_connection")
            fill_input(locators.LocatorElements.db_schema_name, schemaname, clear_first=True)

            self.wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.next_button))).click()
            logger.info("Clicked on Next button!")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.next_button))).click()
            logger.info("Clicked on Next button!")

            click_if_enabled(locators.LocatorElements.ldap_check_box)
            self.wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.next_button))).click()
            logger.info("Clicked on Next button!")

            # TODO: Check if base access

            self.wait.until(EC.presence_of_element_located((By.XPATH, locators.LocatorElements.add_user_or_group)))
            logger.info("Located Add User/Group button!")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.add_user_or_group))).click()
            logger.info("Clicked on Add User/Group button!")
            fill_input(locators.LocatorElements.search_text_box, self.username)
            logger.info(f"Filled the input field by {self.username}")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.search))).click()
            logger.info("Clicked on Search button!")

            self.wait.until(EC.visibility_of_element_located((By.XPATH, locators.LocatorElements.available_users)))
            logger.info("Wait for fetching available users with the given username keyword")
            user_elements = self.cpe_driver.find_elements(By.XPATH, locators.LocatorElements.available_users)
            logger.info("Fetched available users with the given username keyword")
            for user in user_elements:
                if user.text.strip() == self.username:
                    user.click()
                    logger.info(f"Clicked on user: {self.username}")
                    break
            else:
                logger.info(f"User '{self.username}' not found in the grid.")

            button = self.wait.until(EC.presence_of_element_located((By.XPATH, locators.LocatorElements.right_arrow_button)))
            self.cpe_driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
            time.sleep(1)
            self.cpe_driver.execute_script("arguments[0].click();", button)

            self.wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.ok_button))).click()
            self.wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.next_button))).click()
            logger.info("Clicked on Next button!")

            addon_locators = [
                locators.LocatorElements.addon_base_app_extension,
                locators.LocatorElements.addon_content_engine_extension,
                locators.LocatorElements.addon_process_engine_extension,
                locators.LocatorElements.addon_stored_search_extension,
                locators.LocatorElements.addon_workplace_access_extension,
                locators.LocatorElements.addon_workplace_base_extension,
                locators.LocatorElements.addon_workplace_email_extension,
                locators.LocatorElements.addon_workplace_form_extension,
                locators.LocatorElements.addon_workplace_Template_extension,
                locators.LocatorElements.addon_workplace_XT_extension
            ]

            for addon_xpath in addon_locators:
                base_ext_locator = (By.XPATH, addon_xpath)
                element = self.wait.until(EC.presence_of_element_located(base_ext_locator))
                self.cpe_driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                click_if_enabled(addon_xpath)

            self.wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.next_button))).click()
            logger.info("Clicked on Next button!")

            logger.info("Waiting for the 'Add-ons' to be visible")
            self.wait.until(EC.visibility_of_element_located((By.XPATH, locators.LocatorElements.os_add_ons)))
            self.cpe_driver.save_screenshot(f"{self.screenshot_path}/os_add_ons.png")

            self.wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.finish_button))).click()
            logger.info("Clicked on finish button!")
            time.sleep(10)
            self.wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.close))).click()
            logger.info("Clicked on Close button!")

            logger.info("Waiting for the 'Refresh' button to be clickable.")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.object_store_refresh))).click()
            logger.info("Clicked on 'Refresh' button!")

            os_locator = locators.LocatorElements.os_locator.replace("{objectstore}", objectstore)
            logger.info(f"{os_locator}")
            logger.info(f"Waiting for the object store: '{objectstore}' link to be visible.")
            os_element=self.wait.until(EC.visibility_of_element_located((By.XPATH, os_locator)))
            screenshot_path = self.highlighter.highlight_element(self.cpe_driver, os_element, testcase_name=f"{objectstore}")
            logger.info(f"Screenshot saved at: {screenshot_path}")
            logger.info(f"Object Store '{objectstore}' creation completed successfully.")

            object_store_creation = "PASSED"
            return object_store_creation
        
        except Exception as e:
            object_store_creation = "FAILED"
            raise Exception(f"Failed while trying to create object store: {e}")

    def create_object_store(self):
        """
        Method name: create_object_store
        Authors: Anisha Suresh, Nusaiba K K 
        Method Description: Calls fucntion for creating an Object Store in ACCE for all OS in self.args.objectstore.
        Parameters: None
        Returns: None
        Raises:
            ICCSAPSanityTestException: If an exception occurs while creating Object Stores for ICCSAP.
            IERSanityTestException: If an exception occurs while creating Object Stores for IER.
        """
        os_creation = "PASSED"
        object_stores = []
        try:
            for objectstore in self.args.objectstore:
                objectstore = objectstore.strip()
                logger.info(f"{objectstore}")
                os_links = self.wait.until(EC.presence_of_all_elements_located((By.XPATH, locators.LocatorElements.object_stores_list)))
                for link in os_links:
                    label = link.text.strip()
                    object_stores.append(label)
                    logger.info(f"Found ObjectStores: {object_stores}")
                if objectstore in object_stores :
                    os_locator = locators.LocatorElements.os_locator.replace("{objectstore}", objectstore)
                    print(os_locator)
                    os_element = self.wait.until(EC.visibility_of_element_located((By.XPATH, os_locator)))
                    screenshot_path = self.highlighter.highlight_element(self.cpe_driver, os_element, testcase_name=f"{objectstore}")
                    logger.info(f"Screenshot saved at: {screenshot_path}")
                    logger.info("Object Store already created...skipping object store creation")
                elif objectstore not in object_stores:
                    object_store_creation_status = self.create_object_store_form(objectstore)
                    if object_store_creation_status == "FAILED":
                        os_creation = "FAILED"
                        raise Exception(f"Failed to create object store: {e}")
        except Exception as e:
            os_creation = "FAILED"
            if self.product == "ICCSAP":
                raise ICCSAPSanityTestException("Failed while trying to create object store", cause=e) from e
            elif self.product == "IER":
                raise IERSanityTestException("Failed while trying to create object store", cause=e) from e
        finally:
            update_status("os_creation", os_creation, self.product)


    def open_object_store(self, os_name):
        """
        Method name: open_object_store
        Author: Anisha Suresh
        Method Description: Open the given object store.
        Parameters: 
            os_name : Name of the object store to be opened.
        Returns: None
        """ 
        try:
            logger.info("Waiting for the P8DOMAIN Root icon to be clickable")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.p8domain_icon))).click()
            logger.info("Clicked on 'P8DOMAIN' icon.")
            self.cpe.navigate_to_object_store()
            self.cpe.verify_and_capture_object_store(os_name)
            logger.info("Clicked on the object store.")
            self.wait.until(EC.visibility_of_element_located((By.XPATH, locators.LocatorElements.os_check)))
        except Exception as e:
            raise Exception(f"Failed to open object store: {e}")
        
    def navigate_to_root_folder(self):
        """
        Method name: navigate_to_root_folder
        Author: Anisha Suresh
        Method Description: Navigates to Root folder inside the object store.
        Parameters: None
        Returns: None
        """
        try:
            logger.info(f"Waiting for 'Browse' Folder to be clickable.")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.browsefolder))).click()
            logger.info("Clicked on Browse folder")
            logger.info(f"Waiting for Root Folder to be clickable.")
            self.wait.until(EC.element_to_be_clickable((By.LINK_TEXT, 'Root Folder'))).click()
            logger.info("Clicked on Root folder")
            time.sleep(3)
        except Exception as e:
            raise Exception(f"Failed to navigate to Root Folder inside object store: {e}")
            
    def get_object_id(self, element):
        """
        Method name: get_object_id
        Author: Anisha Suresh
        Method Description: Retrieves the object id of the given element
        Parameters: 
            element: Element for which the object_id is to retrieved
        Returns: 
            object_id: Object ID of the element
        """
        object_id = None
        element_id = element.get_attribute("id")
        match = re.search(r'objectId_([A-F0-9-]+)', element_id)
        if match:
            object_id = match.group(1)
            logger.info(f"Object ID is: {object_id}")
        return object_id
    
    def create_new_folder(self, parent_folder, folder_name):
        """
        Method name: create_folder
        Author: Anisha Suresh
        Method Description: Creates a folder in OS.
        Parameters: 
            folder_name : Name of the folder to be created.
        Returns: None
        """
        folder_creation = "FAILED"
        try:
            parent_folder_locator = f'//span[text()="Folder: {parent_folder}"]'
            parent_folder_element = self.wait.until(EC.visibility_of_element_located((By.XPATH, parent_folder_locator)))
            folder_object_id = self.get_object_id(parent_folder_element)

            actions_locator = f'{locators.LocatorElements.root_folder_actions}[contains(@id, "{folder_object_id}")]'
            logger.info(f"Waiting for 'Actions' element: {actions_locator} to be visible.")
            self.wait.until(EC.visibility_of_element_located((By.XPATH, actions_locator))).click()
            logger.info("Clicked on 'Actions' button.")

            new_folder_locator = f'{locators.LocatorElements.new_folder_option}[contains(@id, "{folder_object_id}")]'
            logger.info(f"Waiting for 'New Folder' option: {new_folder_locator} to be clickable.")
            self.wait.until(EC.visibility_of_element_located((By.XPATH, new_folder_locator))).click()
            logger.info("Clicked on 'New Folder'.")

            logger.info("Waiting for 'Define' text to be visible.")
            self.wait.until(EC.visibility_of_element_located((By.XPATH, locators.LocatorElements.define_new_folder)))

            logger.info("Waiting for 'Folder name' field to be available.")
            folder_name_field = self.wait.until(EC.presence_of_element_located((By.XPATH, locators.LocatorElements.new_folder_name)))
            folder_name_field.click()
            logger.info("Clicked on 'Folder name' field.")
            folder_name_field.send_keys(f"{folder_name}")
            logger.info(f"Entered folder name as: {folder_name}")

            logger.info("Waiting for the 'Next' button to be clickable")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.folder_next_button))).click()
            logger.info("Clicked on 'Next' button.")

            logger.info("Waiting for 'Object Properties' element to be visible.")
            self.wait.until(EC.visibility_of_element_located((By.XPATH, locators.LocatorElements.object_properties)))

            logger.info("Waiting for the 'Next' button to be clickable")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.folder_next_button))).click()
            logger.info("Clicked on 'Next' button.")

            logger.info("Waiting for 'Specify Settings' element to be visible.")
            self.wait.until(EC.visibility_of_element_located((By.XPATH, locators.LocatorElements.specify_settings)))
            
            logger.info("Waiting for the 'Next' button to be clickable")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.folder_next_button))).click()
            logger.info("Clicked on 'Next' button.")

            logger.info("Waiting for the 'Finish' button to be clickable")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.folder_finish_button))).click()
            logger.info("Clicked on 'Finish' button.")

            logger.info("Waiting for the 'Success' label to be visible")
            self.wait.until(EC.visibility_of_element_located((By.XPATH, locators.LocatorElements.create_success)))

            logger.info("Waiting for the 'Open' button to be clickable")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.folder_open_wizard))).click()
            logger.info("Clicked on 'Open' button.")

            folder_check = f'//span[contains(text(),"Folder: {folder_name}")]'
            self.wait.until(EC.visibility_of_element_located((By.XPATH, folder_check)))
            
            folder_creation = "PASSED"
            self.cpe_driver.save_screenshot(f'{self.screenshot_path}/{folder_name.lower()}_folder.png')
            return folder_creation
        
        except Exception as e:
            folder_creation = "FAILED"
            raise Exception(f"Failed to create New Folder inside object store: {e}")


    def create_nested_folders_in_root_folder(self, folder_names):
        """
        Method name: create_nested_folders_in_root_folder
        Author: Anisha Suresh
        Method Description: Creates nested folders in the object store.
        Parameters: 
            folder_names: List of folder names in order from outer to inner folders
            os_name : Name of the object store in which folders have to be created.
        Returns: None
        """ 
        for os in self.args.objectstore:
            os = os.strip()
            nested_folders_creation = "PASSED"
            try:
                self.open_object_store(os)
                self.navigate_to_root_folder()
                initial_parent_folder = 'Root Folder'
                parent_folder = initial_parent_folder
                for folder_name in folder_names:
                    folder_creation_status = self.create_new_folder(parent_folder, folder_name)
                    if folder_creation_status == "FAILED":
                        nested_folders_creation = "FAILED"
                        raise Exception(f"Failed to created for {folder_name}")
                    parent_folder = folder_name
            except Exception as e:
                nested_folders_creation = "FAILED"
                if self.product == "ICCSAP":
                    raise ICCSAPSanityTestException("Failed to create nested folders inside object store.", cause=e) from e
            finally:
                update_status("nested_folders_creation", nested_folders_creation, self.product)

    def add_full_control_permissions_to_default_folder(self):
        """
        Method name: add_permissions_to_os
        Author: Anisha Suresh
        Method Description: Add Permissions to user in object store.
        Parameters: 
            os_name: object store for which permissions are granted
        Returns: None
        """
        try:
            logger.info("Waiting for the 'default' folder text to be clickable.")
            default_text_element = self.wait.until(EC.visibility_of_element_located((By.XPATH, locators.LocatorElements.default_folder_text)))
            default_folder_id = self.get_object_id(default_text_element)
            logger.info(f"Object id obtained: {default_folder_id}")
            security_tab_locator = f'{locators.LocatorElements.folder_security_tab}[contains(@id, "{default_folder_id}")]'
            logger.info("Waiting for the 'Security' tab to be clickable.")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, security_tab_locator))).click()
            logger.info("Clicked on the 'Security' tab.")

            logger.info("Waiting for the 'Access Permissions' text to be visible.")
            self.wait.until(EC.visibility_of_element_located((By.XPATH, locators.LocatorElements.access_permissions_text)))
            logger.info("'Access Permissions' text is visible.")

            logger.info("Waiting for the 'Add Permissions' button to be clickable.")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.add_permissions)))

            user_div = f'//td[text()="{self.username}"]/ancestor::div[1]'
            logger.info("Waiting for the user div to be present.")
            user_div_element = self.wait.until(EC.presence_of_element_located((By.XPATH, user_div)))
            user_div_index = user_div_element.get_attribute("rowindex")
            user_checkbox_locator = f'//div[@rowindex={user_div_index}]//span[@role="checkbox"]'

            logger.info("Waiting for the 'User checkbox' to be clickable.")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, user_checkbox_locator))).click()
            logger.info("Clicked on the 'User checkbox'.")
            
            logger.info("Waiting for the 'Edit' button to be clickable.")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.user_permissions_edit_button))).click()
            logger.info("Clicked on the 'Edit' button.")

            logger.info("Waiting for the 'Edit Permissions' text to be visible.")
            self.wait.until(EC.visibility_of_element_located((By.XPATH, locators.LocatorElements.edit_permissions)))

            logger.info("Waiting for the 'Permission Inheritage' dropdown to be clickable.")
            permission_inheritage = self.wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.permission_inheritage)))
            self.cpe_driver.execute_script("arguments[0].scrollIntoView(true);", permission_inheritage)
            permission_inheritage.click()
            logger.info("Clicked on the 'Permission Inheritage' dropdown.")

            logger.info("Waiting for the 'This object and all children' option to be clickable.")
            object_and_all_children = self.wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.object_and_all_children)))
            self.cpe_driver.execute_script("arguments[0].scrollIntoView(true);", object_and_all_children)
            self.cpe_driver.execute_script("arguments[0].click();", object_and_all_children)
            logger.info("Clicked on the 'This object and all children' option.")

            logger.info("Waiting for the 'OK' button to be clickable.")
            ok_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.ok_button)))
            self.cpe_driver.execute_script("arguments[0].scrollIntoView(true);", ok_button)
            self.cpe_driver.execute_script("arguments[0].click();", ok_button)
            logger.info("Clicked on the 'OK' button.")

            logger.info("Waiting for the 'Add Permissions' button to be visible.")
            self.wait.until(EC.visibility_of_element_located((By.XPATH, locators.LocatorElements.add_permissions)))

            self.cpe_driver.save_screenshot(f'{self.screenshot_path}/user_permissions.png')

            logger.info("Waiting for the 'Save' button to be clickable.")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, f'{locators.LocatorElements.folder_save_button}[contains(@id, "{default_folder_id}")]'))).click()
            logger.info("Clicked on the 'Save' button.")

        except Exception as e:
            if self.product == "ICCSAP":
                raise ICCSAPSanityTestException(f"Failed to add full control permissions to user: {self.username} in the object store: {os}", cause=e) from e


    def create_new_property_template(self, property_template_key, property_template_values):
        """
        Method name: create_new_property_template
        Author: Anisha Suresh
        Method Description: Creates new property template.
        Parameters: 
            property_templates: Dictionary of property templates details to be created
        Returns: None
        """ 
        property_template_status = "FAILED"
        try:
            logger.info("Waiting for the 'New' button to be clickable")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.new_prop_temp))).click()
            logger.info("Clicked on 'New' button.")

            logger.info("Waiting for the 'Display Name' field to be clickable")
            display_name = self.wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.property_template_display_name)))
            display_name.click()
            logger.info("Clicked on 'Display Name' field.")
            display_name.clear()
            display_name.send_keys(property_template_key)

            logger.info("Waiting for the 'Description' field to be clickable")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.property_template_description))).click()

            logger.info("Waiting for the 'Next' button to be clickable")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.property_template_next_button))).click()
            logger.info("Clicked on 'Next' button.")

            logger.info("Waiting for the 'Select the Data type' element to be visible")
            data_type = self.wait.until(EC.visibility_of_element_located((By.XPATH, locators.LocatorElements.select_data_type)))

            logger.info("Waiting for the 'Data type' dropdown to be present")
            self.wait.until(EC.presence_of_element_located((By.XPATH, locators.LocatorElements.property_template_data_type_dropdown))).click()
            self.cpe_driver.save_screenshot(f"{self.screenshot_path}/{property_template_key}.png")
            logger.info("Clicked on 'Data type' dropdown.")
            time.sleep(1)

            logger.info("Waiting for the 'String' data type to be visible")
            string_element = self.wait.until(EC.visibility_of_element_located((By.XPATH, locators.LocatorElements.string_data_type)))
            self.cpe_driver.execute_script("arguments[0].scrollIntoView(true);", string_element)
            self.cpe_driver.execute_script("arguments[0].click();", string_element)
            logger.info("Clicked on 'String' data type.")

            logger.info("Waiting for the 'Next' button to be clickable")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.property_template_next_button))).click()
            logger.info("Clicked on 'Next' button.")

            logger.info("Waiting for the 'Select the Marketing type' element to be visible")
            self.wait.until(EC.visibility_of_element_located((By.XPATH, locators.LocatorElements.select_marketing_type)))

            logger.info("Waiting for the 'Next' button to be clickable")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.property_template_next_button))).click()
            logger.info("Clicked on 'Next' button.")

            logger.info("Waiting for the 'Set other attributes' label to be visible")
            self.wait.until(EC.visibility_of_element_located((By.XPATH, locators.LocatorElements.other_attributes_label)))

            logger.info("Waiting for the 'Set Attributes' checklist to be clickable")
            self.wait.until(EC.presence_of_element_located((By.XPATH, locators.LocatorElements.other_attributes))).click()
            logger.info("Clicked on 'Set Attributes' checklist.")

            logger.info("Waiting for the 'Next' button to be clickable")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.property_template_next_button))).click()
            logger.info("Clicked on 'Next' button.")

            logger.info("Waiting for the 'Additional Property template Attributes' element to be visible")
            self.wait.until(EC.visibility_of_element_located((By.XPATH, locators.LocatorElements.additional_property_template)))

            logger.info("Waiting for the Maximum String Length' field to be clickable")
            data_type = self.wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.max_length)))
            self.cpe_driver.execute_script("arguments[0].scrollIntoView(true);", data_type)
            self.cpe_driver.execute_script("arguments[0].click();", data_type)
            logger.info("Clicked on 'Maximum String Length' field.")
            time.sleep(0.2)
            self.cpe_driver.execute_script("arguments[0].focus();", data_type)
            data_type.clear()
            data_type.send_keys(property_template_values['size'])
            data_type.send_keys(Keys.ENTER)
            logger.info(f"Entered maximum string length as as: {property_template_values['size']}.")

            logger.info("Waiting for the 'Next' button to be clickable")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.property_template_next_button))).click()
            logger.info("Clicked on 'Next' button.")

            logger.info("Waiting for the 'Access Rights' element to be visible")
            self.wait.until(EC.visibility_of_element_located((By.XPATH, locators.LocatorElements.access_rights)))

            logger.info("Waiting for the 'Next' button to be clickable")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.property_template_next_button))).click()
            logger.info("Clicked on 'Next' button.")

            logger.info("Waiting for the 'Finish' button to be clickable")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.property_template_finish_button))).click()
            logger.info("Clicked on 'Finish' button.")

            logger.info("Waiting for the 'Success' label to be visible")
            self.wait.until(EC.visibility_of_element_located((By.XPATH, locators.LocatorElements.create_success)))

            self.cpe_driver.save_screenshot(f"{self.screenshot_path}/{property_template_key}1.png")

            logger.info("Waiting for the 'Open' button to be clickable")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.property_template_open_button))).click()
            logger.info("Clicked on 'Open' button.")

            property_template_check_locator = f"//span[contains(text(),'Property Template: {property_template_key}')]"
            logger.info(f"Waiting for the {property_template_key} propery template label to be visible")
            self.wait.until(EC.visibility_of_element_located((By.XPATH, property_template_check_locator)))
            logger.info(f"Waiting for the propery template 'Modification Access' tab to be visible")
            self.wait.until(EC.visibility_of_element_located((By.XPATH, locators.LocatorElements.property_template_modification_access)))

            property_template_status = "PASSED"
            self.cpe_driver.save_screenshot(f"{self.screenshot_path}/{property_template_key}2.png")

            logger.info("Waiting for the 'Close' button to be clickable")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.property_template_close_button))).click()
            logger.info("Clicked on 'Close' button.")
            return property_template_status
        
        except Exception as e:
            property_template_status = "FAILED"
            raise Exception(f"Failed to create property template: {property_template_key}: {e}.")


    def create_property_templates_in_os(self, property_templates, os_name):
        """
        Method name: create_property_templates_in_os
        Author: Anisha Suresh
        Method Description: Creates property templates in the os.
        Parameters: 
            property_templates: Dictionary of all property templates to be created.
            os_name : Name of the object store to be opened.
        Returns: None
        """ 
        property_templates_creation = "PASSED"
        try:
            self.cpe_driver.refresh()
            self.open_object_store(os_name)
            logger.info("Waiting for the 'Data Design' folder to be clickable")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.data_design))).click()
            logger.info("Clicked on 'Data Design' folder.")
            logger.info("Waiting for the 'Property Templates' link to be clickable")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.property_templates))).click()
            logger.info("Clicked on 'Property Templates' link.")
            for key, values in property_templates.items():
                logger.info(f"Creating Property Template: {key}")
                property_template_creation_status = self.create_new_property_template(key, values)
                if property_template_creation_status == "FAILED":
                    property_templates_creation = "FAILED"
                    raise Exception(f"{key} property template creation failed.")
                
            self.cpe_driver.save_screenshot(f'{self.screenshot_path}/property_templates.png')
        except Exception as e:
            property_templates_creation = "FAILED"
            if self.product == "ICCSAP":
                raise ICCSAPSanityTestException("Failed to create property templates inside object store.", cause=e) from e
        
        finally:
            update_status("property_templates_creation", property_templates_creation, self.product)
        

    def navigate_to_doc_classes(self):
        """
        Method name: navigate_to_doc_classes
        Author: Anisha Suresh
        Method Description: Navigates to 'Document Classes' section in the object store.
        Parameters: None
        Returns: None
        """
        try:
            logger.info("Waiting for the 'Data Design' folder to be clickable")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.data_design))).click()
            logger.info("Clicked on 'Data Design' folder.")

            logger.info("Waiting for the 'Classes' link to be clickable")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.data_design_classes))).click()
            logger.info("Clicked on 'Classes' link.")

            logger.info("Waiting for the 'Document Classes' link to be clickable")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.document_class))).click()
            logger.info("Clicked on 'Document Classes' link.")
        except Exception as e:
            raise Exception(f"Failed to navigate to 'Document Classes' in object store: {e}")
    

    def add_property_definitions(self, property_definitions, doc_class_object_id):
        """
        Method name: add_property_definitions
        Author: Anisha Suresh
        Method Description: Add property definitions to the doc class.
        Parameters: 
            property_definitions (list): A list of property definitions to be added.
        Returns: None
        Raises:
            ICCSAPSanityTestException: If there is an error while adding property definitions for the ICCSAP product.
        """ 
        property_definitions_addition = "FAILED"
        try:
            property_definition_locator = f'{locators.LocatorElements.property_definitions}[contains(@id, "{doc_class_object_id}")]'
            logger.info(f"Waiting for the 'Property Definitions' tab: {property_definition_locator} to be clickable")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, property_definition_locator))).click()
            logger.info("Clicked the 'Property Definitions' tab.")

            logger.info("Waiting for the 'Add' button to be visible")
            self.wait.until(EC.visibility_of_element_located((By.XPATH, locators.LocatorElements.property_definitions_add_btn))).click()
            logger.info("Clicked the 'Add' button .")

            for definition in property_definitions:
                definiton_xpath = f"//td[text()='{definition}']"
                definition_element = scroll_element.find_element_in_scroller(self.cpe_driver, locators.LocatorElements.property_definitions_scroller, definiton_xpath, self.product)
                checkbox_element = definition_element.find_element(By.XPATH, "./preceding-sibling::td[1]//span[@role='checkbox']")
                if checkbox_element.get_attribute("aria-checked") != "true":
                    checkbox_element.click()

            logger.info("Waiting for 'OK' button to be available.")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.properties_ok_button))).click()
            logger.info("Clicked the 'OK' button.")

            check_property_definitions = f'//a[text()="{property_definitions[0]}"]'
            logger.info("Waiting for 'check_property_definitions' element to be available.")
            self.wait.until(EC.visibility_of_element_located((By.XPATH, check_property_definitions)))

            property_definitions_save_button = f'//span[text()="Save" and contains(@id, "{doc_class_object_id}")]'
            logger.info("Waiting for the 'Save' button to be clickable.")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, property_definitions_save_button))).click()
            logger.info("Clicked on the 'Save' button.")

            parent_save_locator = f'{property_definitions_save_button}/parent::span'
            logger.info("Waiting for the 'Save' button to be available.")
            self.wait.until(EC.presence_of_element_located((By.XPATH, parent_save_locator)))
            logger.info("Waiting until 'Save' button is disabled")
            self.wait.until(
                lambda d: d.find_element(By.XPATH, parent_save_locator).get_attribute("aria-disabled") == "true"
            )

            logger.info(f"Saving screenshot as: {self.screenshot_path}/property_definitions.png")
            self.cpe_driver.save_screenshot(f'{self.screenshot_path}/property_definitions.png')
            
            property_definitions_addition = "PASSED"
            
        except Exception as e:
            property_definitions_addition = "FAILED"
            if self.product == "ICCSAP":
                raise ICCSAPSanityTestException(f"Failed to add the property definitions: {e}")
        finally:
            update_status("property_definitions_addition", property_definitions_addition, self.product)
            

    def create_sub_document_class_in_os_and_add_property_definitions(self, doc_class, os_name, property_definitions):
        """
        Method name: create_sub_document_class_for_os
        Author: Anisha Suresh
        Method Description: Creates a subclass for the document class in the os.
        Parameters: 
            doc_class: Name of document class to be created.
            os_name : Name of the object store to be opened.
        Returns: None
        """ 
        document_sub_class_creation = "FAILED"
        try:
            self.open_object_store(os_name)
            self.navigate_to_doc_classes()

            logger.info("Waiting for 'Actions' button to be visible.")
            self.wait.until(EC.visibility_of_element_located((By.XPATH, locators.LocatorElements.class_definition_actions))).click()
            logger.info("Clicked on 'Actions' button.")

            logger.info("Waiting for 'New Class' option to be clickable.")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.new_class_option))).click()
            logger.info("Clicked on 'New Class'.")

            logger.info("Waiting for the 'Name and Describe' label to be visible")
            self.wait.until(EC.visibility_of_element_located((By.XPATH, locators.LocatorElements.name_and_describe_class)))

            logger.info("Waiting for the 'Display Name' field to be clickable")
            display_name = self.wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.class_display_name)))
            display_name.click()
            logger.info("Clicked on 'Display Name' field.")
            display_name.clear()
            display_name.send_keys(doc_class)
            logger.info(f"Entered document class name as: {doc_class}")

            logger.info("Waiting for the 'Description' field to be clickable")
            description_element = self.wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.class_definiton_description)))
            self.cpe_driver.execute_script("arguments[0].scrollIntoView(true);", description_element)
            self.cpe_driver.execute_script("arguments[0].click();", description_element)  
            logger.info("Clicked on 'Description' field.")

            logger.info("Waiting for the 'Next' button to be clickable")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.class_next_button))).click()
            logger.info("Clicked on 'Next' button.")

            logger.info("Waiting for the 'Select and Change Object-Value' label to be visible")
            self.wait.until(EC.visibility_of_element_located((By.XPATH, locators.LocatorElements.select_and_change_object_value)))

            logger.info("Waiting for the 'Next' button to be clickable")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.class_next_button))).click()
            logger.info("Clicked on 'Next' button.")

            logger.info("Waiting for the 'Finish' button to be clickable")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.class_definition_finish_button))).click()
            logger.info("Clicked on 'Finish' button.")

            logger.info("Waiting for the 'Success' label to be visible")
            self.wait.until(EC.visibility_of_element_located((By.XPATH, locators.LocatorElements.create_success)))

            logger.info("Waiting for the 'Open' button to be clickable")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.class_open_wizard))).click()
            logger.info("Clicked on 'Open' button.")

            doc_class_verify = f'//*[text()="Class Definition: {doc_class}"]'
            logger.info("Waiting for the 'doc_class_verify' element to be visible")
            doc_class_verify_element = self.wait.until(EC.visibility_of_element_located((By.XPATH, doc_class_verify)))
            doc_class_object_id = self.get_object_id(doc_class_verify_element)

            document_sub_class_creation = "PASSED"
            self.cpe_driver.save_screenshot(f'{self.screenshot_path}/doc_sub_class.png')
            self.add_property_definitions(property_definitions, doc_class_object_id)

        except Exception as e:
            document_sub_class_creation = "FAILED"
            if self.product == "ICCSAP":
                raise ICCSAPSanityTestException(f"Failed to create document sub-class: {doc_class} inside object store.", cause=e) from e
        finally:
            update_status("document_sub_class_creation", document_sub_class_creation, self.product)


    def fetch_db_table_space_from_object_store(self, wait):
        """
        Method name: fetch_db_table_space_from_object_store
        Author: Nusaiba K K 
        Fetch the data-tablespace and Administrative Group from an existing object store.
        Parameters: 
            wait : WebDriver wait.
        Returns:
            tablespace (str) : tablespace name.
            admin_group (str) : Administrative Group name.
        """  
        try:
            
            os_links = wait.until(EC.presence_of_all_elements_located(
                (By.XPATH, locators.LocatorElements.object_stores_list)
            ))

            for link in os_links:
                label = link.text.strip()
                logger.info(f"Found label: {label}")
                if label == "OS01":
                    link.click()
                    logger.info("Clicked on 'OS01' object store.")
                    break
            else:
                logger.info("'OS01' object store not found.")
                return None

            logger.info("Proceed to Administrative -> Workflow -> DB connection steps")
            admin_tab = wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.administrativerfolder)))
            admin_tab.click()
            logger.info("Clicked on 'Administrative' tab.")

            workflow_tab = wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.workflow_system)))
            workflow_tab.click()
            logger.info("Clicked on 'Workflow' tab.")

            conn_input = wait.until(EC.presence_of_element_located((By.XPATH, locators.LocatorElements.database_tablespace)))
            tablespace = conn_input.get_attribute("value").strip().strip("'")
            admin_group_element = wait.until(EC.presence_of_element_located((By.XPATH, locators.LocatorElements.admin_group)))
            admin_group = admin_group_element.get_attribute("value").strip().strip("'")
            logger.info(f"Tablespace and admin_group is: {tablespace,admin_group}")
            wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.close_workflow))).click()
            logger.info("Clicked on Close button!")
            wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.obj_close_button))).click()
            logger.info("Clicked on close button")
            return tablespace,admin_group

        except Exception as e:
            logger.info(f"Error during fetching connection name: {e}")
            return None

    def setup_fpos_workflow(self, wait, tablespace, admin_group,product):
        """
        Method name: setup_fpos_workflow
        Author: Nusaiba K K 
        Description: Selects the FPOS object store and enables workflow on it.
        Parameters:
            wait (WebDriverWait): WebDriver wait object.
            tablespace (str): Tablespace name.
            admin_group (str): Admin group name.
        Returns:
            bool: True if the FPOS object store is selected and workflow is enabled successfully, else False.
        """
        try:
            workflow_system_creation_status = "FAILED"
            wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.refresh_obj_button))).click()
            # Step 1: Select FPOS object store
            os_links = wait.until(EC.presence_of_all_elements_located(
                (By.XPATH, locators.LocatorElements.object_stores_list)
            ))

            for link in os_links:
                label = link.text.strip()
                logger.info(f"Found label: {label}")
                if label == "FPOS":
                    link.click()
                    logger.info("Clicked on 'FPOS' object store.")
                    break
            else:
                logger.info("'FPOS' object store not found.")
                return None

            # Step 2: Enable workflow on FPOS
            admin_tab = wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.administrativerfolder)))
            admin_tab.click()
            logger.info("Clicked on 'Administrative' tab.")
            logger.info("Clicked on Administrative folder.")
            wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.workflow_system))).click()
            logger.info("Clicked on Workflow system.")
            
            try:
                wait.until(EC.invisibility_of_element_located((By.XPATH, locators.LocatorElements.new_workflow_button)))
                wait.until(EC.visibility_of_element_located((By.XPATH, locators.LocatorElements.database_tablespace)))
                self.cpe_driver.save_screenshot(f"{self.screenshot_path}/workflow_system.png")
                logger.info("Workflow system already created...skipping...")
                workflow_system_creation_status = "PASSED"
                return True
            except Exception :
                logger.info("Workflow system not configured yet...proceeding to create.")

                wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.new_workflow_button))).click()
                logger.info("Clicked on New.")

                input_tablespace = wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.database_tablespace)))
                input_tablespace.send_keys(tablespace)
                logger.info("Provided tablespace.")

                input_admin_group = wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.admin_group)))
                input_admin_group.send_keys(admin_group)
                logger.info("Provided admin group.")

                wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.next_button))).click()
                logger.info("Clicked on Next button.")

                input_connection_point_element = wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.connection_point_input)))
                input_connection_point_element.send_keys("PECN")
                logger.info("Provided connection name.")

                wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.next_button))).click()
                logger.info("Clicked on Next button.")

                isolated_region_name_element = wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.isolated_region_name)))
                isolated_region_name_element.clear()
                isolated_region_name_element.send_keys("ISO")
                logger.info("Provided isolated region name.")

                isolated_region_number_element = wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.isolated_region_number)))
                isolated_region_number_element.clear()
                isolated_region_number_element.send_keys("1")
                logger.info("Provided isolated region number.")

                wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.next_button))).click()
                logger.info("Clicked on Next button.")
                wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.next_button))).click()
                logger.info("Clicked on Next button.")
                wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.finish_button))).click()
                logger.info("Clicked on Finish button.")
                wait.until(EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.close_workflow)))
                self.cpe_driver.save_screenshot(f"{self.screenshot_path}/workflow_system.png")
                workflow_system_creation_status = "PASSED"
                return workflow_system_creation_status

        except Exception as e:
            workflow_system_creation_status = "FAILED"
            logger.error(f"Error in setup_fpos_workflow: {e}")
            raise IERSanityTestException("Failed to create workflow system", cause=e) from e
        finally:
            update_status("Creation of workflow system",workflow_system_creation_status,product)
        
    def quit_browser(self):
        """
        Method name: quit_browser
        Author: Anisha Suresh
        Description: Quits the browser.
        Parameters: None
        Returns: None
        """ 
        try:
            browser_manager = BrowserManager(self.cpe_driver)
            browser_manager.quit_browser()
        except Exception as e:
            if self.product == "ICCSAP":
                raise ICCSAPSanityTestException(f"Failed to quit the cpe browser.", cause=e) from e

    def ier_acce_runner(self):
        """
        Method name: ier_acce_runner
        Description : Function to automate the creation and configuration of an Object Store.

        Steps performed:
        1. Retrieves application credentials for login.
        2. Validates the presence of username, password, and object store name(s).
        3. Navigates to the Object Store section in the CPE (Content Platform Engine) web UI.
        4. Iterates over one or more provided object store names to create them using the UI form.
        5. Fetches database tablespace and admin group details from the configured object store.
        6. Selects the FPOS (FileNet P8 Object Store) object store.
        7. Enables workflow functionality on the selected FPOS using the extracted configuration.

        The function ensures that the web browser driver is closed at the end of execution.
        """
        try:
            self.login_and_navigate_to_os()
            self.create_object_store()
            tablespace, admin_group = self.fetch_db_table_space_from_object_store(self.wait)
            self.setup_fpos_workflow(self.wait, tablespace, admin_group,"IER")
        except Exception as e:
            raise IERSanityTestException("Failed during configuring ACCE", cause=e) from e
        finally:
            logger.info("Quitting browser...")
            self.cpe_driver.quit()

if __name__ == "__main__":
    acce = ACCE()
    acce.ier_acce_runner()
