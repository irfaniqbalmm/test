import base64
import json
import os
import platform
import re
import subprocess
import sys

from tomlkit import parse

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from component_sanity_tests.exceptions.sanity_exception import SanityTestException
from utils.login import fetch_and_decode_secret
from utils.logger import logger

def run_oc_command(commands):
    """
    Method name: run_oc_command
    Author: Anisha Suresh (anisha-suresh@ibm.com)
    Description: Runs an oc command 
    Parameters:
        commands : Commands to be run
    Returns:
        stdout from oc command / exception if any
    """
    try:
        # Join commands with '&&' for batch execution
        command = " && ".join(commands)
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout
        else:
            return f"Error: {result.stderr}"
    except Exception as e:
        logger.error(f"An exception occured during running the oc command-{command} : {e}")

def insert_credentials(url_template, username, password):
    """
    Method name: insert_credentials
    Author: Anisha Suresh (anisha-suresh@ibm.com)
    Description: Inserts the appLoginCredentials into the urls so that pop-ups can be handled using selenium
    Parameters:
        url_template : initial url
        username : AppLoginUsername of the deployment
        password : AppLoginPassword of the deployment
    Returns:
        modified url
    """
    protocol, rest = url_template.split('://', 1)
    return f"{protocol}://{username}:{password}@{rest}"


def get_opensearch_secret_from_cm(deployment_type, urls, value):
    """
    Method name: get_opensearch_secret_from_cm
    Author: Anisha Suresh (anisha-suresh@ibm.com)
    Description: Fetches the OpenSearch connection secret from the provided value string and stores it in the 'opensearch_secret' key of the provided urls dictionary.
    Parameters:
        urls (dict): A dictionary containing the connection details.
        value (str): A string containing the access information from which to extract the secret.
    Returns: None
    """
    logger.info("Fetching OpenSearch Connection secret from bai-access-info")
    if deployment_type.lower() == "starter":
        username_match = re.search(r'OpenSearch Username:\s*(\S+)', value)
        password_match = re.search(r'OpenSearch Password:\s*(\S+)', value)
        if username_match:
            logger.info(f"Matched string: 'OpenSearch Username' in access-info")
            urls["opensearch_username"] = username_match.group(1)
        if password_match:
            logger.info(f"Matched string: 'OpenSearch Password' in access-info")
            urls["opensearch_password"] = password_match.group(1)
        logger.info(f'Fetched opensearch credentials: {urls["opensearch_username"]}/{urls["opensearch_password"]}')
    else:
        match = re.search(r'OpenSearch connection secret:\s*(\S+)', value)
        if match:
            logger.info(f"Matched string: 'OpenSearch connection secret' in access-info")
            urls["opensearch_secret"] = match.group(1)
            logger.info(f"Matched string: 'OpenSearch connection secret' in access-info")
        logger.info(f'Fetched opensearch secret: {urls["opensearch_secret"]}')


def get_elasticsearch_credentials(namespace):
    """
    Method name: get_elasticsearch_credentials
    Author: Anisha Suresh (anisha-suresh@ibm.com)
    Description: Get the elasticsearch/opensearch login credentials & decode them from base64 format.
    Parameters:
        namespace : namespace where the opensearch instance is deployed
    Returns:
        opensearch_username : opensearch login username 
        opensearch_password : opensearch login password
    """
    logger.info("Fetching opensearch/elasticsearch credentials ...")

    possible_secrets = [
        ("opensearch-admin-user", "opensearch-admin"),
        ("opensearch-credentials", "admin"),
        ("opensearch-ibm-elasticsearch-cred-secret", "elastic"),
        ("iaf-system-elasticsearch-es-default-user", "username", "password"),
    ]
    
    for secret in possible_secrets:
        try:
            if len(secret) == 2:
                opensearch_username = secret[1]
                opensearch_password = fetch_and_decode_secret(secret[0], opensearch_username, namespace)
            else:
                logger.warning(f"Couldn't fetch opensearch credentials, Trying with elasticsearch.")
                opensearch_username = fetch_and_decode_secret(secret[0], secret[1], namespace)
                opensearch_password = fetch_and_decode_secret(secret[0], secret[2], namespace)

            logger.info(f"Credentials for opensearch/elasticsearch are : {opensearch_username}/{opensearch_password}")
            return opensearch_username, opensearch_password
        
        except Exception as e:
            logger.warning(f"Failed to fetch opensearch/elasticsearch  credentials from {secret[0]}: {e}")
            continue

    logger.error("Failed to fetch any opensearch/elasticsearch credentials.")
    return None, None


def get_opensearch_credentials(urls, namespace):
    try : 
        opensearch_uname,opensearch_pwd = None, None
        if urls["opensearch_secret"]:
            logger.info(f'Fetching opensearch credentials from secret: {urls["opensearch_secret"]}')
            secret = urls["opensearch_secret"]
            command = [
                'oc', 'get', 'secret', secret,
                '-n', namespace, '-o', 'json']
            try:
                logger.info(f"Running command: {command}")
                output = subprocess.run(command, capture_output=True, text=True, check=True).stdout.strip()
                secret_json = json.loads(output)
                secret_data = secret_json.get("data", {})
                if not secret_data:
                    raise ValueError("No data found in secret")
                logger.info(f"Output: {secret_data}")
                opensearch_uname, encoded_password = next(iter(secret_data.items()))
                opensearch_pwd = base64.b64decode(encoded_password).decode('utf-8')
                logger.info(f"Opensearch credentials fetched: {opensearch_uname}/{opensearch_pwd}")
            except Exception as e:
                raise RuntimeError(f"An error occured while fetching {secret} secret: {e}.")
        elif urls["opensearch_username"] and urls["opensearch_password"]:
            opensearch_uname = urls["opensearch_username"]
            opensearch_pwd = urls["opensearch_password"]
        else:
            opensearch_uname,opensearch_pwd = get_elasticsearch_credentials(namespace)
    except Exception as e:
        logger.error(f"An exception occured during opensearch/elasticsearch credential fetch : {e}")
    return opensearch_uname,opensearch_pwd


def fetch_endpoints(config_file="./inputs/config.toml", is_sanity=False) :
    """
    Method name: fetch_endpoints
    Author: Anisha Suresh (anisha-suresh@ibm.com)
    Description: Fetchs the endpoints from the ocp cluster and inserts credentials in the url to handle pop-ups in Selenium.
    Parameters: None
    Returns: None
    """
    try:
        logger.info("==========================================Starting execution of fetch_endpoints in endpoints.py==========================================")
        logger.info("Fetching endpoints from access-configmap...")
        global access_cm_name

        with open(config_file, "r") as file :
            config=parse(file.read())

        namespace = config['configurations']['project_name']
        deployment_type = config['configurations']['deployment_type']
        app_login_username = config['credentials']['app_login_username']
        app_login_password = config['credentials']['app_login_password']

        # Initialize variables
        ocp_url = config['ocp_paths']['ocp']
        config_maps_url = config['ocp_paths']['config_maps']
        logger.info("Fetched ocp url and configmaps url from config.toml file")

        # Initialize URL variables
        logger.info("Initialising other urls to None value...")
        urls = {
            "ocp_url": ocp_url,
            "config_maps_url": config_maps_url,
            "iccsap_route": None,
            "iccsap_files_route": None,
            "bai_desktop_route": None,
            "cmis_route": None,
            "cmis_ocp_route": None,
            "cpeadmin_route": None,
            "cpehealthcheck_route": None,
            "cpepingpage_route": None,
            "FileNet_Process_Services_ping_page": None,
            "FileNet_Process_Services_details_page": None,
            "FileNet_P8_Content_Engine_Web_Service_page": None,
            "FileNet_Process_Engine_Web_Service_page": None,
            "Content_Search_Services_health_check": None,
            "cpe_stateless_health_legacy_route": None,
            "cpe_stateless_ping_route": None,
            "Stless_FileNet_Process_Services_ping_page": None,
            "Stless_FileNet_Process_Services_details_page": None,
            "Stless_FileNet_P8_Content_Engine_Web_Service_page": None,
            "Stless_FileNet_Process_Engine_Web_Service_page": None,
            "Stless_Content_Search_Services_health_check": None,
            "graphql_route": None,
            "ier_route": None,
            "navigator_route": None,
            "navigator_second_link2": None,
            "taskmanager_route": None,
            "opensearch_url": None,
            "opensearch_secret": None,
            "opensearch-username": None,
            "opensearch-password": None
        }

        # Define a mapping from description to URL name
        logger.info("Defining a mapping from components to their respective URL name...")
        mapping = {
            "Content Platform Engine administration": "cpeadmin_route",
            "Content Platform Engine health check": "cpe_stateless_health_legacy_route",
            "Content Platform Engine ping page": "cpe_stateless_ping_route",
            "FileNet Process Services ping page": "Stless_FileNet_Process_Services_ping_page",
            "FileNet Process Services details page": "Stless_FileNet_Process_Services_details_page",
            "FileNet P8 Content Engine Web Service page": "Stless_FileNet_P8_Content_Engine_Web_Service_page",
            "FileNet Process Engine Web Service(PEWS) page": "Stless_FileNet_Process_Engine_Web_Service_page",
            "Content Search Services health check": "Stless_Content_Search_Services_health_check",
            "Content Management Interoperability Services for CP4BA": "cmis_route",
            "Content Management Interoperability Services for CP4BA (OCP route)": "cmis_ocp_route",
            "Content Services GraphQL": "graphql_route",
            "Content Collector for SAP SSL Webport URL": "iccsap_route",
            "Content Collector for SAP Plugin URL": "iccsap_files_route",
            "BAI Desktop": "bai_desktop_route",
            "Business Automation Navigator for CP4BA": "navigator_route",
            "Business Automation Navigator for FNCM": "navigator_second_link2",
            "Task Manager": "taskmanager_route",
            "OpenSearch URL": "opensearch_url",
            "OpenSearch connection secret": "opensearch_secret",
            "Elasticsearch URL": "opensearch_url",
            "OpenSearch Username": "opensearch-username",
            "OpenSearch Password": "opensearch-password"
        }
            
        # Get the ConfigMap name containing access info
        logger.info("Fetching exact access-info configmap name and data from the cluster...")
        if platform.system() == 'Windows' :

            def get_configmap_data():
                # Command to list ConfigMaps and filter by name containing 'access-info'
                command = f'oc get configmaps --no-headers=true | findstr access-info'
                try:
                    result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
                    # Check if any ConfigMap was found
                    if not result.stdout.strip():
                        logger.error("No 'access-info' configmap found.")
                        logger.critical("Exiting BVT execution!!")
                        exit()
                    access_cm_name = result.stdout.strip().split()[0]  # Assuming the first result is the desired ConfigMap name
                    logger.info(f"The access-info configmap name fetched is : {access_cm_name}")
                    get_data_command = f'oc get configmap {access_cm_name} -o json'
                    data_result = subprocess.run(get_data_command, shell=True, check=True, capture_output=True, text=True)
                    configmap_json = json.loads(data_result.stdout)
                    configmap_data = configmap_json.get('data', {})
                    return access_cm_name,configmap_data
                except subprocess.CalledProcessError as e:
                    logger.error(f"Error executing command: {command}")
                    logger.error(f"Error : {e}")
                    return None,None
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing JSON output: {data_result.stdout}")
                    logger.error(f"Error : {e}")
                    return None,None
            access_cm_name, data = get_configmap_data()
        else :
            access_cm_name = run_oc_command([f"oc get cm | grep access-info | awk '{{print $1}}'"]).strip()
            access_info = run_oc_command([f"oc get cm {access_cm_name} -o jsonpath='{{.data}}'"])
            data = json.loads(access_info)
        logger.info(f"Fetched name of access-info configmap  : {access_cm_name}")
        logger.info("Completed fetching exact access-info configmap name and data from the cluster...")

        # Assign URLs to variables based on the description
        logger.info("Assigning urls to component variables ...")
        for key, value in data.items():
            matches = re.findall(r'(.+?): (https?://[^\s]+)', value)
            for description, url in matches:
                if description in mapping:
                    urls[mapping[description]] = url
            if "bai-access" in key:
                get_opensearch_secret_from_cm(deployment_type, urls, value)

        opensearch_uname,opensearch_pwd = get_opensearch_credentials(urls, namespace)
        
        # Access CPE ACCESS INFO separately
        cpe_access_info = run_oc_command([f"oc get cm {access_cm_name} -n {namespace} -o jsonpath='{{.data.cpe-access-info}}'"])
        cpe_mapping = {
            "Content Platform Engine health check": "cpehealthcheck_route",
            "Content Platform Engine ping page": "cpepingpage_route",
            "FileNet Process Services ping page": "FileNet_Process_Services_ping_page",
            "FileNet Process Services details page": "FileNet_Process_Services_details_page",
            "FileNet P8 Content Engine Web Service page": "FileNet_P8_Content_Engine_Web_Service_page",
            "FileNet Process Engine Web Service(PEWS) page": "FileNet_Process_Engine_Web_Service_page",
            "Content Search Services health check": "Content_Search_Services_health_check",
        }
        cpe_matches = re.findall(r'(.+?): (https?://[^\s]+)', cpe_access_info)
        for description, url in cpe_matches:
            if description in cpe_mapping:
                if url.endswith("'"):
                    urls[cpe_mapping[description]] = url.strip("'")
                else :
                    urls[cpe_mapping[description]] = url

        # Get IER route separately as it does not have a description
        ier_url = run_oc_command([f"oc get cm {access_cm_name} -n {namespace} -o jsonpath='{{.data.ier-access-info}}'"])
        if ier_url.startswith("'") and ier_url.endswith("'"):
            urls["ier_route"] = ier_url.strip("'")
        else :
            urls["ier_route"] = ier_url

        # Miscellaneous URLs
        if urls['graphql_route'] :
            urls["graphql_ping_route"] = f"{urls['graphql_route']}/ping"
        if urls["cmis_ocp_route"] :
            urls["cmis_ocp_route"] = insert_credentials(urls["cmis_ocp_route"], app_login_username,app_login_password)
        if not is_sanity:
            if urls["navigator_route"] :
                urls["navigator_cmod_route"] = f"{urls['navigator_route']}?desktop={config['cmod']['cmod_desktop_name']}"
            if urls["navigator_route"] :
                urls["navigator_cm8_route"] = f"{urls['navigator_route']}?desktop={config['cm8']['cm8_desktop_name']}"
            if urls["navigator_route"] :
                urls["navigator_cmod_route_upgrade"] = f"{urls['navigator_route']}?desktop={config['cmod']['u_cmod_desktop_name']}"
            if urls["navigator_route"] :
                urls["navigator_cm8_route_upgrade"] = f"{urls['navigator_route']}?desktop={config['cm8']['u_cm8_desktop_name']}"
        if urls["navigator_second_link2"] :
            urls["navigator_second_link"] = insert_credentials(urls['navigator_second_link2'], app_login_username,app_login_password)
        if urls["opensearch_url"] :
            urls["opensearch_url"] = insert_credentials(urls['opensearch_url'], opensearch_uname, opensearch_pwd)
        if urls["FileNet_Process_Services_ping_page"] :
            urls["FileNet_Process_Services_ping_page"] = insert_credentials(urls['FileNet_Process_Services_ping_page'], app_login_username,app_login_password)
        if urls["Stless_FileNet_Process_Services_ping_page"] :
            urls["Stless_FileNet_Process_Services_ping_page"] = insert_credentials(urls['Stless_FileNet_Process_Services_ping_page'], app_login_username,app_login_password)

        # Save the URLs to a JSON file
        logger.info("Saving urls to endpoints.json file ...")
        try :
            with open('./inputs/endpoints.json', 'w') as json_file:
                json.dump(urls, json_file, indent=4)
            logger.info("Saved endponts to json file.")
        except Exception as e :
            logger.error(f"An exception occured while writing endpoints : {e}")
            logger.critical("Exiting BVT Execution!!")
            exit()
        finally :
            logger.info("==========================================Ended execution of fetch_endpoints in endpoints.py==========================================\n\n")
    except Exception as e:
        if is_sanity:
            raise SanityTestException("Failed to prepare the config file", cause=e) from e
        logger.exception(f"An exception occured while trying to fetch the endpoints: {e}")
        
if __name__ == '__main__' :
    fetch_endpoints()
