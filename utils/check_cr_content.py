import os
import sys
import subprocess
import yaml
import json

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tomlkit import parse
from utils.bvt_status import update_status
from utils.logger import logger

# Fetching deployment type and build from conifg.toml file
global deployment_type, build
with open("./inputs/config.toml","r") as file :
    config = parse(file.read())
deployment_type = config['configurations']['deployment_type']
build = config['configurations']['build']

def get_cr_data() :
    """
    Method name: get_cr_data
    Author: Anisha Suresh (anisha-suresh@ibm.com)
    Description: Get the CR file content from cluster
    Parameters: None
    Returns:
        file_content (yaml) : CR content
    """
    if deployment_type == 'starter' or "21.0.3" in build:
        try : 
            file_content = subprocess.check_output(["oc","get","ICP4ACluster","-o","yaml"], universal_newlines=True)
        except :
            file_content = subprocess.check_output(["oc","get","Content","-o","yaml"], universal_newlines=True)
    else :
        file_content = subprocess.check_output(["oc","get","Content","-o","yaml"], universal_newlines=True)
    return file_content

def check_cr_content(keyword):
    """
    Method name: check_cr_content
    Author: Anisha Suresh (anisha-suresh@ibm.com)
    Description: Check if a particular content is present in the CR file
    Parameters:
        keyword : content to be checked
    Returns:
        keyword value / False
    """
    try:
        logger.info(f"Checking if {keyword} is present in CR...")
        file_content = get_cr_data()
        return keyword in file_content
    except Exception as e:
        logger.info(f"{keyword} is NOT present in CR.")
        logger.info(f"Exception occured during fetching cr content : {e}")
        return False
    
def check_egress_cr_parameter(parameter):
    """
    Method name: check_egress_cr_parameter
    Author: Anisha Suresh (anisha-suresh@ibm.com)
    Description: Checks if the egress parameter is set to True in the CR
    Parameters:
        parameter (str): The parameter to check in the CR content.
    Returns:
        str: The egress label, either "True" or "False".
    Raises:
        None
    """
    egress_label = "None"
    if check_cr_content(parameter): 
        egress_label = "True"
        logger.warning("Egress label is True. Egress is enabled.")
    else:
        egress_label = "False"
        logger.warning("Egress label is False. Egress is disabled.")
    return egress_label

def check_egress() :
    """
    Method name: check_egress
    Author: Anisha Suresh (anisha-suresh@ibm.com)
    Description: Check if egress is enabled or not
    Parameters:
        None
    Returns:
        True / False
    """
    logger.info("Checking egress label ...")
    egress_status = "None"
    if "21.0.3" in build :
        pass
    elif build in ["22.0.2", "23.0.1", "23.0.2", "24.0.0", "24.0.1"]:
        egress_status = check_egress_cr_parameter("sc_restricted_internet_access: true")
    else:
        egress_status = check_egress_cr_parameter("sc_generate_sample_network_policies: true")
    update_status("egress",egress_status)
    return egress_status

def check_fips() :
    """
    Method name: check_fips
    Author: Anisha Suresh (anisha-suresh@ibm.com)
    Description: Check if fips is enabled or not
    Parameters:
        None
    Returns:
        True / False
    """
    logger.info("Checking if FIPS is enabled or not ... ")
    if check_cr_content("enable_fips: false"): 
        fips = "False"
        logger.warning("FIPS is disabled.")
    else:
        fips = "True"
        logger.warning("FIPS is enabled.")
    update_status("fips",fips)
    return fips

def get_optional_components(cr_content=None, retry=False) :
    """
    Method name: get_optional_components
    Author: Anisha Suresh (anisha-suresh@ibm.com)
    Description: Return the optional components from CR file
    Parameters:
        cr_content (yaml) : CR file content, default = None
        retry (boolean) : Retry if True, default = False
    Returns:
        optional_components_list : List of optional components
    """
    try:
        optional_components_list = []
        logger.info("Getting list of optional components ...")
        file_content = cr_content if cr_content else get_cr_data()
        cr_data = yaml.safe_load(file_content)
        items = cr_data.get('items', [])
        for item in items:
            spec = item.get('spec', {})
            shared_config = spec.get('shared_configuration',{})
            optional_components = spec.get('content_optional_components') or shared_config.get('sc_optional_components')
            logger.info(f"Optional components fetched : {optional_components}")
            if optional_components is None:
                if not retry:
                    logger.warning("Optional components couldn't be fetched.")
                    """
                        If this exception hits, it might be a upgrade from 21.0.3 
                        so optional components are in ICP4ACluster CR.
                    """
                    try:
                        logger.info("Trying with ICP4ACluster.")
                        cp4a_content = subprocess.check_output(["oc","get","ICP4ACluster","-o","yaml"], universal_newlines=True)
                        return get_optional_components(cr_content=cp4a_content,retry=True)
                    except subprocess.CalledProcessError as e:
                        logger.error(f"Failed to fetch ICP4ACluster data: {e}")
                        return []  
                logger.error("ICP4ACluster check already attempted. No optional components found.")
            if isinstance(optional_components, str) :
                optional_components_list.extend(comp.upper() for comp in optional_components.split(','))
            elif isinstance(optional_components, list) or isinstance(optional_components, dict):
                optional_components_list.extend(comp.upper() for comp in optional_components)
            else:
                logger.error("Unexpected format for optional components.")
        if not optional_components_list:
            logger.error("Couldn't fetch optional components. Returning an empty list.")
            return []
        logger.info(f"Optional components deployed are : {optional_components_list}")
    except Exception as e:
        logger.error(f"An exception occured while fetching optional components : {e}")
    return optional_components_list

def get_conn_point(initialize_config, cr_param):
    """
    Method name: get_conn_point
    Author: Anisha Suresh (anisha-suresh@ibm.com)
    Description: Fetches the connection point value from the initialization configuration.
    Parameters:
        initialize_config: Dictionary containing initialization configuration details.
        cr_param: Parameter key to fetch from the object store configuration.
    Returns:
        cr_param_value: Value of the requested parameter if found, otherwise None.
    Raises:
        Exception: If an error occurs while fetching the value from the object store.
    """
    cr_param_value = None
    ic_obj_store_creation = initialize_config.get('ic_obj_store_creation', {})
    if not isinstance(ic_obj_store_creation, dict):
        logger.error("ic_obj_store_creation is not a valid dictionary.")
        return cr_param_value
    
    object_stores = ic_obj_store_creation.get('object_stores', [])
    if object_stores and isinstance(object_stores, list) and len(object_stores) > 0:
        try:
            cr_param_value = object_stores[0].get(cr_param)
            logger.info(f"{cr_param} is: {cr_param_value}")
        except KeyError:
            logger.error(f"Key '{cr_param}' not found in object store.")
        except Exception as e:
            logger.error(f"An error occurred while getting details from object store: {e}")
    else:
        logger.warning("No object stores found in initialization configuration.")
    return cr_param_value

def get_initialization_values(cr_param, dep_type=deployment_type):
    """
    Method name: get_initialization_values
    Author: Anisha Suresh (anisha-suresh@ibm.com)
    Description: Return the initialization parameter value from CR file
    Parameters:
        cr_param: Parameter from CR whose value has to be fetched.
        dep_type: Deployment type
    Returns:
        cr_param_value: Value of parameter
    Raises:
        Exception: If execution of fetching value fails
    """
    cr_param_value = None
    try:
        file_content = get_cr_data()
        cr_data = yaml.safe_load(file_content)
        items = cr_data.get('items', [])
        
        for item in items:
            spec = item.get('spec', {})
            if not isinstance(spec, dict):
                logger.error("Spec section is missing or invalid in CR.")
                continue
            
            initialize_config = spec.get('initialize_configuration', {})
            if initialize_config:
                cr_param_value = get_conn_point(initialize_config, cr_param)
                if cr_param_value is not None:
                    return cr_param_value
            else:
                logger.info("Couldn't fetch init config from CR.")
                
                if dep_type.lower() == "post-upgrade":
                    logger.info(f"Retrying from last applied config since deployment type is: {dep_type}.")
                    try:
                        pre_init_config_yaml = subprocess.check_output(
                            ["oc", "get", "cm", "ibm-cp4ba-content-shared-info", "-o", "jsonpath={.data.pre_initialize_configuration}"],
                            universal_newlines=True
                        )
                        pre_init_config = yaml.safe_load(pre_init_config_yaml)
                        if pre_init_config:
                            cr_param_value = get_conn_point(pre_init_config, cr_param)
                    except subprocess.CalledProcessError as e:
                        logger.error(f"Failed to fetch pre-initialization configuration: {e}")
                    except yaml.YAMLError as e:
                        logger.error(f"Error parsing YAML from pre-initialization configuration: {e}")
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML from CR file: {e}")
    except Exception as e:
        logger.error(f"An exception occurred while trying to fetch object store details from CR: {e}")
    return cr_param_value

def get_object_store_details() :
    """
    Method name: get_object_store_details
    Author: Anisha Suresh (anisha-suresh@ibm.com)
    Description: Return the object store details from CR file
    Parameters:
        None
    Returns:
        DB details from OS
    """
    logger.info("Getting object store details ... ")
    try:
        db_schema_name = get_initialization_values('oc_cpe_obj_store_schema_name')
        db_table_loc = get_initialization_values('oc_cpe_obj_store_table_storage_location')
        db_index_loc = get_initialization_values('oc_cpe_obj_store_index_storage_location')
        db_lob_loc = get_initialization_values('oc_cpe_obj_store_lob_storage_location')

        # Assigning None if empty string
        db_schema_name = db_schema_name or None
        db_table_loc = db_table_loc or None
        db_index_loc = db_index_loc or None
        db_lob_loc = db_lob_loc or None

        logger.info(f"DB Schema name is : {db_schema_name}")
        logger.info(f"DB Table location is : {db_table_loc}")
        logger.info(f"DB Index location is : {db_index_loc}")
        logger.info(f"DB LOB location is : {db_lob_loc}")
        return [db_schema_name,db_table_loc,db_index_loc,db_lob_loc]
    except Exception as e:
        logger.error(f"An exception occured while trying to fetch object store details from CR : {e}")
        return
    
def get_jvm_customize_options(component,cr_data):
    """
    Method name: get_jvm_customize_options
    Author: Anisha Suresh (anisha-suresh@ibm.com)
    Description: Fetch the jvm customised options of the component from CR file
    Parameters:
        component (str) : compoennt for which the jvm options has to be fetched
        cr_data (yaml) : CR content
    Returns:
        jvm_customize_options : JVM customised options from CR
    """
    try:
        component = component.lower()
        param = f"{component}_production_setting"
        logger.info(f"Checking the {param} parameter is present in CR.")
        if param in str(cr_data):
            logger.info(f"{param} parameter is present in the CR.")
            items = cr_data.get('items', [])
            logger.info("Checking if jvm options is present in the CR")
            for item in items:
                spec = item.get('spec', {})
                ecm_config = spec.get('ecm_configuration', {})
                component_config = ecm_config.get(component, {})
                component_product_setting = component_config.get(f'{component}_production_setting', {})
                if 'jvm_customize_options' in component_product_setting :
                    jvm_customize_options = component_product_setting.get('jvm_customize_options', {})
                    logger.info(f"{component.upper()} JVM custom options found : {jvm_customize_options}")
                    return jvm_customize_options
                else :
                    logger.debug("JVM options is not present.")
                    return
        else :
            logger.debug(f"{param} parameter is NOT present in the CR.")
            return
    except Exception as e:
        logger.error(f"An exception occured while trying to fetch the jvm options : {e}")
        return

if __name__ == "__main__" :
    egress_label = "none"
    fips = "none"
    check_fips()
    if "21.0.3" in build :
        logger.warning('21.0.3 has no Egress Network policy.')
    else :
        egress_label = check_egress()
    get_optional_components()
    get_object_store_details()
