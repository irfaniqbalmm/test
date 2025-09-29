import sys
import os
# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import subprocess
import yaml
from utils.logger import logger

def get_db_ldap(deployment_type,build):
    """
    Method name: get_db_ldap
    Description: Return the type of DB & LDAP from CR file
    Parameters:
        None
    Returns:
        db_type : type of DB
        ldap_type : type of LDAP
    """
    logger.info("Fetching database and ldap details from CR file...")
    try:
        db_type = "None" 
        ldap_type = "None"
        if deployment_type == 'starter' :
            logger.info("Deployment type is Starter!")
            logger.info("Setting LDAP as Open LDAP and DB as PostgreSQL")
            return "PostgreSQL","Open LDAP"
        elif "21.0.3" in build :
            logger.info("Getting ICP4ACluster CR ...")
            file_content = subprocess.check_output(["oc", "get", "ICP4ACluster", "-o", "yaml"], universal_newlines=True)
        else :
            logger.info("Getting Content CR ...")
            file_content = subprocess.check_output(["oc","get","Content","-o","yaml"], universal_newlines=True)
        cr_data = yaml.safe_load(file_content)
        logger.info("Loaded CR data into cr_data variable.")
        # finding db type
        logger.info("Fetching Database type used... ")
        try :
            items = cr_data.get('items', [])
            for item in items:
                spec = item.get('spec', {})
                db_config = spec.get('datasource_configuration', {})
                dc_gcd_datasource = db_config.get('dc_gcd_datasource', {})
                db_type = dc_gcd_datasource.get('dc_database_type', []).upper()
                logger.info(f"DB is : {db_type}")
        except Exception as e:
            logger.error("Couldn't find DB type")
            logger.error(f"An exception occured during fetch DB type : {e}")
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
        return db_type,ldap_type
    except Exception as e:
        logger.error(f"An exception occurred while trying to fetch DB and LDAP details : {e}")