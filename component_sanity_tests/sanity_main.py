import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from component_sanity_tests.exceptions.sanity_exception import SanityTestException
from component_sanity_tests.utils.common_utils.prepare_config import PrepareConfiguration
from utils.logger import logger
import utils.login as login
import utils.endpoints as endpoints

def main():
    """
    Method name :   main
    Author      :   Anisha Suresh (anisha-suresh@ibm.com)
    Description :   This method is the entry point for the sanity tests. 
                    It prepares the env for sanity tests by logging into the cluster 
                    preparing the config file and fetching required details.
    Parameters  :   None
    Returns     :   None
    """

    INIT_CONFIG_FILE = "./component_sanity_tests/config/config.ini"
    CONFIG_FILE = "./component_sanity_tests/config/config.toml"

    try:
        login.ocp_login(INIT_CONFIG_FILE)
    except SanityTestException as e:
        logger.error(f"An exception occured during logging into cluster: {e}")

    try:
        prepare_config = PrepareConfiguration(INIT_CONFIG_FILE, CONFIG_FILE)
        prepare_config.prepare_config_file()
    except SanityTestException as e:
        logger.error(f"An exception occured during preparing the config file: {e}")

    try:
        endpoints.fetch_endpoints(CONFIG_FILE, True)
    except SanityTestException as e:
        logger.error(f"An exception occured during fetching the endpoints: {e}")
    
if __name__ == "__main__":
    main()