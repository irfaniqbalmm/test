import requests
from requests.auth import HTTPBasicAuth
from logs import DeploymentLogs
import json
import time
import os
import configparser

log = DeploymentLogs()
parser = configparser.ConfigParser(interpolation=None)
current_dir = os.getcwd()
parser.read(current_dir + '/config/data.config')

def test_fyre_connection():
    """
        Name: test_fyre_connection
        Author: Dhanesh
        Desc: To test the fyre API connection
        Parameters:
            none
        Returns:
            none
        Raises:
            RequestException, Exception
    """
    # Define API endpoint and credentials
    url = parser.get('FYRE', 'connection_url')
    username = parser.get('FYRE', 'username')
    password = parser.get('FYRE', 'password')

    # Set authentication and other parameters
    auth = HTTPBasicAuth(username, password)
    verify = False  # Set to False to ignore SSL certificate verification
    timeout = 10  # Set a timeout to avoid waiting indefinitely
    try:
        # Make the GET request
        response = requests.get(url, auth=auth, verify=verify, timeout=timeout)
        print(json.dumps(response.json(), indent=4))
        log.logger.info(json.dumps(response.json(), indent=4))
        # Check if the request was successful
        if response.status_code == 200:
            print("Fyre API connection successful.")
            log.logger.info("Fyre API connection successful.")
        else:
            log.logger.info(f"Fyre API connection failed with status code {response.status_code}.")
            raise Exception(f"Fyre API connection failed with status code {response.status_code}.")
    except requests.exceptions.RequestException as e:
        log.logger.info(f"An error occurred while testing the connection: {e}")
        raise Exception(f"An error occurred while testing the connection: {e}")

def create_quick_burn():
    """
        Name: create_quick_burn
        Author: Dhanesh
        Desc: To create a new ocp fyre quick burn cluster
        Parameters:
            none
        Returns:
            credentials
        Raises:
            RequestException, Exception
    """
    # Define API endpoint and credentials
    url = parser.get('FYRE', 'quickburn_url').strip()
    print(f'URL: {url}')
    username = parser.get('FYRE', 'username').strip()
    print(f'Username: {username}')
    password = parser.get('FYRE', 'password').strip()
    print(f'Password: {password}')
    quickburn_name = parser.get('FYRE', 'quickburn_name').strip().lower()
    print(f'Quickburn name: {quickburn_name}')
    ocp_version = parser.get('FYRE', 'ocp_version').strip()
    print(f'OCP version: {ocp_version}')

    # Set authentication and other parameters
    auth = HTTPBasicAuth(username, password)
    verify = False  # Set to False to ignore SSL certificate verification
    timeout = 180  # Set a timeout to avoid waiting indefinitely

    # Define the JSON payload
    # Available parameters
    """
    {
        "site": "<svl/rtp, default will be svl>",
        "name": "<name, default will be picked from a pool>",
        "description": "<description, default will just be left blank>",
        "platform": "<platform, default is x>",
        "quota_type": "<product_group/quick_burn, default is product_group>",
        "time_to_live": "<hours, required if quota_type is quick_burn>",
        "size":"<medium/large, required if quota_type is quick_burn>",
        "product_group_id": "<id, default is your default product group>",
        "ocp_version": "<version, default is latest version on selected platform>",
        "expiration": "<hours, default is blank, remove if you want no expiration>",
        "haproxy": {
            "timeout": {
                "http-request": "10s",
                "queue": "1m",
                "connect": "10s",
                "client": "1m",
                "server": "1m",
                "http-keep-alive": "10s",
                "check": "10s"
            }
        },
        "fips": "<yes/no, default is no>",   // enables FIPS mode
        "ip_sec": "<yes/no, default is no>", // enables IPsec network encryption
        "ocp_network_type": "<type, default is OVNKubernetes (OpenshiftSDN deprecated as of 4.14)>",
        "ocp_cluster_network": "<network, default is 10.254.0.0/16>", //improper definition can also impact other users
        "ocp_service_network": "<network, default is 172.30.0.0/16>", //improper definition can also impact other users
        "pull_secret": "<pull_secret>",
        "ssh_key": "<ssh_key>", // will accept either an array – ["<ssh_key>",..] – or a comma separated list
        "master":  {
            "cpu": "<count, default is 8, max is 16>",
            "memory": "<GB, default is 16, max is 64>",
            "base_disk_size": "<GB, default is 100, min is 40, max is 500>"
        },
        "worker":  [
            {
                "count": "<count, default is 3>",
                "cpu": "<count, default is 8, max is 16>",
                "memory": "<GB, default is 16, max is 64>",
                "base_disk_size": "<GB, default is 250, min is 40, max is 500>",
                "additional_disk":  [
                    "<size, default is 200, max is 1000>",
                    "<size, default is 200, max is 1000>"
                ]
            }
        ]
    }
    """

    payload = {
        "name": quickburn_name,
        "ocp_version": ocp_version,
        "platform": "x",
        "quota_type": "quick_burn",
        "size": "large",
        "time_to_live": "36",
        "fips": "yes"
    }

    try:
        # Make the POST request and create new quick burn cluster
        response = requests.post(url, auth=auth, verify=verify, json=payload, timeout=timeout)
        print(json.dumps(response.json(), indent=4))
        log.logger.info(json.dumps(response.json(), indent=4))
        # Check if the request was successful
        if response.status_code == 200:
            print("Cluster build initiated successfully.")
            log.logger.info("Cluster build initiated successfully..")
        else:
            log.logger.info(f"Quick burn creation failed with status code {response.status_code}.")
            raise Exception(f"Quick burn creation failed with status code {response.status_code}.")
        
        # Wait until the cluster creation gets completed and return the cluster details
        try:
            i = 1
            flag = False
            for i in range(1, 10):
                get_clusters = requests.get(url, auth=auth, verify=verify, timeout=timeout)
                print(json.dumps(get_clusters.json(), indent=4))
                log.logger.info(json.dumps(get_clusters.json(), indent=4))
                cluster_details = get_clusters.json()
                for cluster in cluster_details['clusters']:
                    cluster_name = cluster['cluster_name']
                    print(f'Cluster name: {cluster_name}')
                    if cluster_name == quickburn_name:
                        flag = True
                        deployment_status = cluster['deployment_status']
                        if deployment_status == 'configuring':
                            print('Configuring quickburn cluster is in progress. Waiting for 10 min before next retry.')
                            log.logger.info('Configuring quickburn cluster is in progress. Waiting for 10 min before next retry.')
                            time.sleep(600) #Wait for 10 min before another retry
                            i += 1
                            print(f'Retrying {i} time.....')
                            log.logger.info(f'Retrying {i} time.....')
                        elif deployment_status == 'deployed':
                            print('Quickburn cluster configured successfully')
                            log.logger.info('Quickburn cluster configured successfully')
                            access_url = cluster['access_url']
                            ocp_username = cluster['ocp_username']
                            kubeadmin_password = cluster['kubeadmin_password']
                            credentials = {
                                'access_url': access_url,
                                'ocp_username': ocp_username,
                                'kubeadmin_password': kubeadmin_password
                            }
                            print(f'The credentials of the {quickburn_name} are:')
                            log.logger.info(f'The credentials of the {quickburn_name} are:')
                            for key, value in credentials.items():
                                print(f'{key}: {value}')
                                log.logger.info(f'{key}: {value}')
                            return credentials
                        else:
                            print(f'Unknown status while creating quickburn: {deployment_status}')
                            log.logger.info(f'Unknown status while creating quickburn: {deployment_status}')
                            raise ValueError(f'Unknown status while creating quickburn: {deployment_status}')
                
                if flag is False:
                    raise ValueError(f'The created ocp cluster {quickburn_name} is not present in the list of clusters')

        except requests.exceptions.RequestException as e:
            log.logger.info(f"An error occurred while fetching the quick burn: {e}")
            raise Exception(f"An error occurred while fetching the quick burn: {e}") 
        
    except requests.exceptions.RequestException as e:
        log.logger.info(f"An error occurred while creating the quick burn: {e}")
        raise Exception(f"An error occurred while creating the quick burn: {e}")

def save_credentials(credentials):
    """
        Name: save_credentials
        Author: Dhanesh
        Desc: To save the credentials to a json file
        Parameters:
            none
        Returns:
            none
        Raises:
            Exception
    """
    try:
        current_dir = os.getcwd()
        credentials_file = current_dir + '/config/quickburn.json'
        with open(credentials_file, 'x') as file:
            json.dump(credentials, file)
            log.logger.info(f"Saved {credentials} to {credentials_file}")
            print(f"Saved {credentials} to {credentials_file}")
    except FileExistsError:
        raise ValueError(f"File already exists: {credentials_file}")
    except Exception as e:
        log.logger.error(f"An error occurred while writing the credentials to {credentials_file}: {e}")
        raise ValueError(f"An error occurred while writing the credentials to {credentials_file}: {e}")


if __name__=='__main__':
    test_fyre_connection()
    credentials = create_quick_burn()
    save_credentials(credentials)
