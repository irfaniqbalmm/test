import sys
import os
# Add the project root to sys.path
sys.path.append(os.getcwd())
import subprocess
from utils.logger import logger

def get_ldap_from_bai_deployment():
    """
    Method name: get_ldap_from_bai_deployment
    Author: Dhanesh
    Description: Return the type of DB & LDAP from CR file
    Parameters:
        None
    Returns:
        db_type : type of DB
        ldap_type : type of LDAP
    """
    logger.info("Fetching ldap details from CR file...")
    try:
        ldap_type = "None"
        logger.info("Getting bai CR ...")
        file_content = subprocess.check_output(["oc","get","InsightsEngine","-o","yaml"], universal_newlines=True)
        
        # finding ldap type
        logger.info("Fetching LDAP type ...")
        try :
            if 'ad:' in file_content :
                ldap_type = "MSAD"
            elif 'tds:' in file_content :
                ldap_type = "TDS"
            logger.info(f"LDAP is : {ldap_type}")
        except Exception as e:
            logger.error("Couldn't find LDAP type")
            logger.error(f"An exception occured during fetching LDAP type : {e}")
        return ldap_type
    except Exception as e:
        logger.error(f"An exception occurred while trying to fetch DB and LDAP details : {e}")