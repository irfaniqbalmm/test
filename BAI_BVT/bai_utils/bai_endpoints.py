import json
import os
import platform 
import re
import subprocess
import sys

from tomlkit import parse

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from utils.endpoints import run_oc_command, insert_credentials, get_opensearch_secret_from_cm, get_opensearch_credentials
from utils.logger import logger

def fetch_bai_access_info_endpoints():
    """
    Method name: fetch_bai_access_info_endpoints
    Author: Dhanesh
    Description: To fetch the endpoints from the access-info file
    Parameters:
        commands : None
    Returns:
        stdout from oc command / exception if any
    """
    logger.info("==========================================Starting execution of fetch_endpoints==========================================")
    logger.info("Fetching endpoints from bai-bai-access-configmap...")
    global access_cm_name

    with open("./BAI_BVT/resources/config.toml","r") as file :
        config=parse(file.read())
    
    # Initialize variables
    namespace = config['configurations']['project_name']
    deployment_type = config['configurations']['deployment_type']
    ocp_url = config['ocp_paths']['ocp']
    config_maps_url = config['ocp_paths']['config_maps']
    logger.info("Fetched ocp url and configmaps url from ./BAI_BVT/resources/config.toml file")

    # Initialize URL variables
    logger.info("Initialising other urls to None value...")
    urls = {
        "ocp_url": ocp_url,
        "config_maps_url": config_maps_url,
        "bai_desktop_route": None,
        "kafka_bootstrap_servers": None,
        "kafka_sasl_mechanism": None,
        "kafka_security_protocol": None,
        "opensearch_url": None,
        "opensearch_secret": None,
        "opensearch-username": None,
        "opensearch-password": None
    }

    # Define a mapping from description to URL name
    logger.info("Defining a mapping from components to their respective URL name...")
    mapping = {
        "Business Performance Center URL": "bai_desktop_route",
        "OpenSearch URL": "opensearch_url",
        "Kafka Bootstrap_Servers": "kafka_bootstrap_servers",
        "Kafka Sasl Mechanism": "kafka_sasl_mechanism",
        "Kafka Security Protocol": "kafka_security_protocol",
        "OpenSearch connection secret": "opensearch_secret",
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
        matches = re.findall(r'(.+?): (.+)', value)
        for description, url in matches:
            if description in mapping:
                urls[mapping[description]] = url
        if "bai-access" in key:
            get_opensearch_secret_from_cm(deployment_type, urls, value)

    try : 
        opensearch_uname,opensearch_pwd =  get_opensearch_credentials(urls, namespace)
    except Exception as e:
        logger.info(f"An exception occured during opensearch credential fetch : {e}")
    
    if urls["opensearch_url"] :
        urls["opensearch_url"] = insert_credentials(urls["opensearch_url"], opensearch_uname, opensearch_pwd)

    # Save the URLs to a JSON file
    logger.info("Saving urls to ./BAI_BVT/resources/endpoints.json file ...")
    try :
        with open('./BAI_BVT/resources/endpoints.json', 'w') as json_file:
            json.dump(urls, json_file, indent=4)
        logger.info("Saved endponts to ./BAI_BVT/resources/endpoints.json file.")
    except Exception as e :
        logger.error(f"An exception occured while writing endpoints : {e}")
        logger.critical("Exiting BVT Execution!!")
        exit()
    finally :
        logger.info("==========================================Ended execution of fetch_endpoints in endpoints.py==========================================\n\n")


if __name__ == "__main__":
    fetch_bai_access_info_endpoints()

