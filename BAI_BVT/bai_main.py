import os
import sys

sys.path.append(os.getcwd())

import bai_utils.bai_endpoints as access_info
import bai_utils.bai_input_data as input_data
from bai_exception import BAIBVTException, BAIMVTException
from bai_utils.bai_clear_data import DeleteData
from BAI_BVT.driver.launch_driver import ChromeDriverSingleton
from BAI_BVT.test_cases.bai_standalone_tests import Test
import mvt.contentMVT as contentMVT
import reports.pdf_report as pdf_report
import utils.login as login
from utils.clear_history_cache_cookies import ClearChrome
from utils.logger import logger

def main():
    """
        Name: main
        Desc: main method to call the tests
        Parameters:
        Returns:
            None
        Raises:
            None
    """
    #Logging into the ocp
    try : 
        login.ocp_login('./BAI_BVT/resources/config.ini')
    except Exception as e:
        raise BAIBVTException("Error occured while logging into the cluster") from e
    
    #Write data to the config.toml file
    try : 
        input_data.write_input_data()
    except Exception as e:
        raise BAIBVTException("Error occured while writing input data to ./BAI_BVT/resources/config.toml") from e
    
    try:
        clean = DeleteData()
        clean.reset_execution_data()
    except Exception as e:
        raise BAIBVTException("Error occured while deleting the previous execution data") from e

    # Fetch the bai-bai-access-info
    try : 
        access_info.fetch_bai_access_info_endpoints()
    except Exception as e:
        raise BAIBVTException("Error occured while fetching the bai-bai-access-info") from e
    
    # Verify access info and its contents
    try :
        access_info_test = Test()
        access_info_test.verify_access_info_config_map()
        access_info_test.verify_access_info_contents()
    except Exception as e:
        exception =  BAIBVTException('Failed to verify bai access info contents', e)
        logger.error(f'An error occured during access info bvt {exception}')
    finally:
        ChromeDriverSingleton.closeBrowser()

    # Verify installed operators are successful
    try:
        installed_operators_test = Test()
        installed_operators_test.verify_installed_operators()
    except Exception as e:
        exception =  BAIBVTException('Failed to verify installed operators', e)
        logger.error(f'An error occured during installed operators bvt {exception}')
    finally:
        ChromeDriverSingleton.closeBrowser()

    # Verify bai login, content and navigator dashboard
    try:
        bai_bpc_test = Test()
        bai_bpc_test.verify_bai_login(15)
        bai_bpc_test.verify_content_dashboard()
        bai_bpc_test.verify_navigator_dashboard()
    except Exception as e:
        exception =  BAIBVTException('Failed to verify bai bpc dashboard', e)
        logger.error(f'An error occured during bai bpc dashboard bvt {exception}')
    finally:
        ChromeDriverSingleton.closeBrowser()
    
    # Verify opensearch url
    try:
        test = Test()
        test.verify_opensearch()
    except Exception as e:
        exception =  BAIBVTException('Failed to verify opensearch url', e)
        logger.error(f'An error occured during opensearch bvt {exception}')
    finally:
        ChromeDriverSingleton.closeBrowser()

    # Verify bai operator log
    try:
        test.verify_bai_operator_log()
    except Exception as e:
        exception =  BAIBVTException('Failed to verify bai operator log', e)
        logger.error(f'An error occured during log verification: {exception}')

    #Convert html to pdf report
    try:
        pdf_report.convert_html_to_pdf("./BAI_BVT/resources/config.toml")
    except Exception as e:
        raise BAIBVTException("Error occured while converting html to pdf", e)

    #MVT 
    try : 
        contentMVT.mvt_runner("BAIS", True)
    except Exception as e:
        raise BAIMVTException("Error occured while executing MVT", e)

    
if __name__ == "__main__":
    main()
