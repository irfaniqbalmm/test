import os
import sys
import shutil

from tomlkit import parse

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from component_pages.ier.ier import IERDownloader

from component_sanity_tests.exceptions.ier_exception import IERSanityTestException
from component_sanity_tests.tests.icn import ICN
from inputs.locators import LocatorElements
from utils.logger import logger

class IER:
    def __init__(self, config_file):
        """
        Method name: __init__
        Author: Nusaiba K K
        Description : Initialize the IER class.
        Parameters:
            config_file: Path to the configuration file
        Returns:None
        """
        with open(config_file, "r") as file:
            self.config = parse(file.read())

        self.namespace = self.config['configurations']['project_name']
        self.icn = ICN("IER",config_file)

    def login_to_icn(self):
        """
        Method name: login_to_icn
        Author: Nusaiba K K and Anisha Suresh
        Description :  Login to ICN and navigate to the administration page.
        Parameters:None
        Returns:None
        """
        try:
            self.icn.login_and_navigate_to_administration()
        except IERSanityTestException as e:
            logger.error(f"Login to Navigator failed: {e}")

    
    def call_create_plugin_function(self):
        """
        Method name: call_create_plugin_function
        Author: Nusaiba K K and Anisha Suresh
        Description :  Call the create plugin function.
        Parameters:None
        Returns:None
        """
        try:
            self.icn.create_plugin()
        except IERSanityTestException as e:
            logger.error(f"IER plugin creation failed: {e}")

    def call_create_repo_function(self):
        """
        Method name: call_create_repo_function
        Author: Nusaiba K K and Anisha Suresh
        Description :  Call the create repository function.
        Parameters:None
        Returns:None
        """
        try:
            fncm_repo_locator = LocatorElements.fncm_repo
            self.icn.create_product_repo("FPOS", fncm_repo_locator, "FPOS")
            self.icn.create_product_repo("ROS", fncm_repo_locator, "ROS")
        except IERSanityTestException as e:
            logger.error(f"Failed during IER repo creation: {e}")

    def call_create_desktop_function(self):
        """
        Method name: call_create_desktop_function
        Author: Nusaiba K K and Anisha Suresh
        Description :  Call the create desktop function.
        Parameters:None
        Returns:None
        """
        try:
            self.icn.create_product_desktop("IER_DSK", "FPOS")
            self.icn.create_product_desktop("ICN_DSK", "ROS")
        except IERSanityTestException as e:
            logger.error(f"IER desktop creation failed: {e}")

    def call_tm_configure_function(self):
        """
        Method name: call_tm_configure_function
        Author: Nusaiba K K and Anisha Suresh
        Description :  Call the TM configure function.
        Parameters:None
        Returns:None
        """
        try:
            self.icn.configure_tm()
        except IERSanityTestException as e:
            logger.error(f"IER TM configuration failed: {e}")

    def call_load_desktop_function(self, desktop_name):
        """
        Method name: call_load_desktop_function  
        Author: Nusaiba K K  
        Description: Call the function to load the specified desktop.  
        Parameters:
            desktop_name (str): Name of the desktop to load (e.g., 'ICNDESK', 'IERDESK')  
        Returns: None
        """
        try:
            self.icn.load_desktop(desktop_name)
        except IERSanityTestException as e:
            logger.error(f"{desktop_name} Desktop loading failed: {e}")
    
    def ier_icn_runner(self):
        """
        Method name: ier_icn_runner
        Author: Nusaiba K K and Anisha Suresh
        Description: Runs the complete IER configuration flow in Navigator.
        """
        ier_downloader = IERDownloader(is_sanity=True)
        ier_downloader.setup_driver()
        ier_downloader.close_driver()
        self.login_to_icn()
        self.call_create_plugin_function()
        self.call_create_repo_function()
        self.call_create_desktop_function()
        self.call_tm_configure_function()
        self.call_load_desktop_function("ICNDSK")
        self.call_load_desktop_function("IERDSK")
        