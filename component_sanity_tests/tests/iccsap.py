from types import SimpleNamespace
import os
import sys

from tomlkit import parse

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from component_pages.iccsap import ICCSAP
from component_sanity_tests.exceptions.iccsap_exception import ICCSAPSanityTestException
from component_sanity_tests.tests.icn import ICN
from component_sanity_tests.tests.acce import ACCE
from component_sanity_tests.utils.iccsap import prepare_profile
from inputs.locators import LocatorElements
from utils.logger import logger

class ICCSAPSanity:
    def __init__(self, config_file):
        """
        Method name: __init__
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Initializes the ICCSAPSanity class
        Parameters:
            None
        Returns:
            None
        """
        self.config_file = config_file
        with open(config_file, "r") as file :
            self.config = parse(file.read())
        
        self.namespace = self.config['configurations']['project_name']
        
        self.product = "ICCSAP"
        self.objectstores = ["ICCSAPOSTEST"]
        self.doc_class = "ICCSAPDOC"
        self.repository_name = "ICCSAP"
        self.desktop_name = "ICCSAP"
        self.archiving_profile_name = "Sanity Archiving Profile"
        self.acce_params = SimpleNamespace(objectstore=self.objectstores, config_file_path=self.config_file, product="ICCSAP")

    def download_iccsap_jar_files(self):
        """
        Method name: download_iccsap_jar_files
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Calls the function to download the ICCSAP jar files.
        Parameters:
            None
        Returns:
            None
        """
        try:
            self.iccsap = ICCSAP(self.config_file)
            self.iccsap.navigate_to_iccsap()
            self.iccsap.close_browser()
        except ICCSAPSanityTestException as e:
            logger.error(f"ICCSAP jar files download failed: {e}")

    def login_to_acce(self):
        """
        Method name: login_to_acce
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Calls the function to login to the CPE and navigate to Object Stores.
        Parameters:
            None
        Returns:
            None
        """
        try :
            self.acce = ACCE(self.acce_params)
            self.acce.login_and_navigate_to_os()
        except ICCSAPSanityTestException as e :
            logger.error(f"Login to CPE failed: {e}")

    def call_create_iccsap_os_function(self):
        """
        Method name: call_create_iccsap_os_fucntion
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Calls the function to create Objectstore.
        Parameters:
            None
        Returns:
            None
        """
        try :
            self.acce.create_object_store()
        except ICCSAPSanityTestException as e :
            logger.error(f"Object store creation failed: {e}")

    def call_nested_folder_creation_function(self):
        """
        Method name: call_nested_folder_creation_function
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Calls the function to create nested folders in Rott folder of the Objectstore.
        Parameters:
            None
        Returns:
            None
        """
        try :
            self.acce.create_nested_folders_in_root_folder(["ICCSAP", "default"])
        except ICCSAPSanityTestException as e :
            logger.error(f"Folder creation failed: {e}")

    def call_add_permissions_function(self):
        """
        Method name: call_create_iccsap_os_fucntion
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Calls the function to create Objectstore.
        Parameters:
            None
        Returns:
            None
        """
        try :
            self.acce.add_full_control_permissions_to_default_folder()
        except ICCSAPSanityTestException as e :
            logger.error(f"Adding permissions to object store failed: {e}")

    def call_property_templates_creation_function(self):
        """
        Method name: call_nested_folder_creation_function
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Calls the function to create property templates..
        Parameters:
            None
        Returns:
            None
        """
        try:
            property_templates_for_iccsap = {
                'ALFdpages' : {'data_type': 'String', 'size': 3},
                'ALFpages' : {'data_type': 'String', 'size': 3},
                'Barcode' : {'data_type': 'String', 'size': 40},
                'PageSize' : {'data_type': 'String', 'size': 239},
                'SAPCompCharset' : {'data_type': 'String', 'size': 239},
                'SAPCompCreated' : {'data_type': 'String', 'size': 239},
                'SAPCompModified' : {'data_type': 'String', 'size': 239},
                'SAPComps' : {'data_type': 'String', 'size': 239},
                'SAPCompSize' : {'data_type': 'String', 'size': 239},
                'SAPCompVersion' : {'data_type': 'String', 'size': 239},
                'SAPContType' : {'data_type': 'String', 'size': 239},
                'SAPDocDate' : {'data_type': 'String', 'size': 239},
                'SAPDocId' : {'data_type': 'String', 'size': 40},
                'SAPDocProt' : {'data_type': 'String', 'size': 4},
                'SAPType' : {'data_type': 'String', 'size': 3},
            }
            self.acce.create_property_templates_in_os(property_templates_for_iccsap, self.objectstores[0])
        except ICCSAPSanityTestException as e:
            logger.error(f"Property templates creation failed: {e}")

    def call_document_class_creation_function(self):
        """
        Method name: call_document_class_creation_function
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Calls the function to create document sub-class.
        Parameters:
            None
        Returns:
            None
        """
        try :
            property_definitions = [
                'ALFdpages',
                'ALFpages',
                'Barcode',
                'PageSize',
                'SAPCompCharset',
                'SAPCompCreated',
                'SAPCompModified',
                'SAPComps',
                'SAPCompSize',
                'SAPCompVersion',
                'SAPContType',
                'SAPDocDate',
                'SAPDocId',
                'SAPDocProt',
                'SAPType',
            ]
            self.acce.create_sub_document_class_in_os_and_add_property_definitions("ICCSAPDOC", self.objectstores[0], property_definitions)
        except ICCSAPSanityTestException as e :
            logger.error(f"Document subclass creation failed: {e}")

    def call_acce_quit_browser_function(self):
        """
        Method name: call_document_class_creation_function
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Calls the function to quite the acce browser.
        Parameters:
            None
        Returns:
            None
        """
        try :
            self.acce.quit_browser()
        except ICCSAPSanityTestException as e :
            logger.error(f"Quitting CPE browser failed: {e}")

    def initialize_and_login_to_icn(self) :
        """
        Method name: initialize_and_login_to_icn
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Calls the function to login to the Navigator.
        Parameters:
            None
        Returns:
            None
        """
        try :
            self.icn = ICN(self.product, self.config_file)
            self.icn.login_and_navigate_to_administration()
        except ICCSAPSanityTestException as e :
            logger.error(f"Login to navigator failed: {e}")
        
    def call_create_plugin_function(self):
        """
        Method name: call_create_plugin_function
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Calls the function to create ICCSAP plugin in the Navigator.
        Parameters:
            None
        Returns:
            None
        """
        try :
            self.icn.create_plugin()
        except ICCSAPSanityTestException as e :
            logger.error(f"ICCSAP plugin creation failed: {e}")


    def call_create_repo_function(self):
        """
        Method name: call_create_repo_function
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Calls the function to create ICCSAP repository in the Navigator.
        Parameters:
            None
        Returns:
            None
        """
        try :
            fncm_repo_locator = LocatorElements.fncm_repo
            self.icn.create_product_repo("ICCSAP", fncm_repo_locator, self.objectstores[0])
        except ICCSAPSanityTestException as e :
            logger.error(f"Failed during calling function for ICCSAP repo creation: {e}")

    def call_create_desktop_function(self):
        """
        Method name: call_create_desktop_function
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Calls the function to create ICCSAP repository in the Navigator.
        Parameters:
            None
        Returns:
            None
        """
        try :
            self.icn.create_product_desktop("ICCSAP", "ICCSAP")
        except ICCSAPSanityTestException as e :
            logger.error(f"ICCSAP desktop creation failed: {e}")

    def call_tm_configure_function(self):
        """
        Method name: call_tm_configure_function
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Calls the function to create ICCSAP repository in the Navigator.
        Parameters:
            None
        Returns:
            None
        """
        try :
            self.icn.configure_tm()
        except ICCSAPSanityTestException as e :
            logger.error(f"ICCSAP TM configuration failed: {e}")

    def call_profile_prepare_function(self):
        """
        Method name: call_profile_prepare_fucntion
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Calls the function to prepare ICCSAP profile to import in the ICCSAP desktop.
        Parameters:
            None
        Returns:
            None
        """
        try:
            self.prepare = prepare_profile.PrepareProfile(self.config_file)
            self.iccsap_profile_file_path = self.prepare.prepare_profile()
        except ICCSAPSanityTestException as e :
            logger.error(f"ICCSAP profile preparing failed: {e}")
        

    def call_profile_import_function(self):
        """
        Method name: call_profile_prepare_fucntion
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Calls the function to prepare ICCSAP profile to import in the ICCSAP desktop.
        Parameters:
            None
        Returns:
            None
        """
        try:
            self.icn.import_and_start_iccsap_server_profile(self.iccsap_profile_file_path, "ICCSAP")
        except ICCSAPSanityTestException as e :
            logger.error(f"ICCSAP profile import and start failed: {e}")
        
    def call_archiving_profile_creation_function(self):
        """
        Method name: call_profile_prepare_fucntion
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Calls the function to create archiving profile in the ICCSAP desktop.
        Parameters:
            None
        Returns:
            None
        """
        try:
            self.icn.create_new_archiving_profile("Sanity Archiving Profile", "ICCSAPDOC", "/opt/ibm/iccsap/instance/SamplePictures")
        except ICCSAPSanityTestException as e :
            logger.error(f"ICCSAP new archiving profile creation failed: {e}")
        
    def call_archiving_tasks_creation_function(self):
        """
        Method name: call_profile_prepare_fucntion
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Calls the function to create archiving tasks in the ICCSAP desktop.
        Parameters:
            None
        Returns:
            None
        """
        try:
            self.icn.create_archiving_tasks("Sanity Archiving Profile")
        except ICCSAPSanityTestException as e :
            logger.error(f"ICCSAP archiving tasks creation failed: {e}")

    def call_profile_restore_function(self):
        """
        Method name: call_profile_prepare_fucntion
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Calls the function to prepare ICCSAP profile to import in the ICCSAP desktop.
        Parameters:
            None
        Returns:
            None
        """
        try:
            self.iccsap_profile_file_path = self.prepare.restore_profile()
        except ICCSAPSanityTestException as e :
            logger.error(f"ICCSAP profile preparing failed: {e}")

    def call_nav_quit_browser_function(self):
        """
        Method name: call_document_class_creation_function
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Calls the function to quite the acce browser.
        Parameters:
            None
        Returns:
            None
        """
        try :
            self.icn.quit_browser()
        except ICCSAPSanityTestException as e :
            logger.error(f"Quitting ICN browser failed: {e}")

        
        
if __name__ == "__main__":
    iccsap = ICCSAPSanity()
    iccsap.download_iccsap_jar_files()
    iccsap.login_to_acce()
    iccsap.call_create_iccsap_os_function()
    iccsap.call_add_permissions_function()
    iccsap.call_nested_folder_creation_function()
    iccsap.call_property_templates_creation_function()
    iccsap.call_document_class_creation_function()
    iccsap.call_acce_quit_browser_function()
    iccsap.initialize_and_login_to_icn()
    iccsap.call_create_plugin_function()
    iccsap.call_create_repo_function()
    iccsap.call_create_desktop_function()
    iccsap.call_tm_configure_function()
    iccsap.call_profile_prepare_function()
    iccsap.call_profile_import_function()
    iccsap.call_archiving_profile_creation_function()
    iccsap.call_nav_quit_browser_function()