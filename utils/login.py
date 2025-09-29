import base64
import configparser
import json
import os
import re
import subprocess
import sys

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from component_sanity_tests.exceptions.sanity_exception import SanityTestException
from utils.logger import logger

login_cache = None
cred_cache = None
opensearch_cred_cache = None

def ocp_login(file_name=None) :
    """
    Method name: ocp_login
    Description: Perform oc login using the kubeadmin user and password.
                 If cluster details are not added in the clusters.json file exists the execution.
    Parameters:
        None
    Returns:
        None
    """
    try:
        logger.info("==========================================Starting OC Login==========================================")
        global login_cache
        logger.info("Performing oc login using the kubeadmin user and password. If cluster details are not added in the clusters.json file, the execution exists.")
        if file_name is None:
            logger.info(f'setting the file path to: {file_name}')
            file_name = 'config.ini'
        config = configparser.ConfigParser()
        config.read(file_name)
        logger.info(f"Reading currrent cluster selected from {file_name} file")
        cluster = config.get('configurations', 'cluster')
        logger.info(f"Cluster used to run BVT : {cluster}")
        project_name = config.get('configurations', 'project_name')
        logger.info(f"BVT running namespace : {project_name}")
        quick_kube_pwd = config.get('configurations','quick_burn_pwd',fallback=None)
        if quick_kube_pwd: 
            password = quick_kube_pwd
            logger.info(f"Quick Burn KUBE Login password : {password}")
        else :
            f = open('clusters.json')
            cluster_data = json.load(f)
            cluster_found = 0
            for i in cluster_data :
                if str(i).lower() == cluster.lower() :
                    cluster_found = 1
                    password = cluster_data[i]['kube_pwd']
            if cluster_found == 0 :
                logger.error("Add cluster details to cluster.json file.")
                logger.critical("Exiting BVT execution.")
                exit()
        if login_cache == None :
            get_project = subprocess.Popen(['oc', 'project'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            logger.info("Logging into OCP Cluster...")
            output, error = get_project.communicate()
            if output or error :
                logger.info(output) if output else logger.error(error)
            string = f"Using project \"{project_name}\" on server \"https://api.{cluster}.cp.fyre.ibm.com:6443\".\n" 
            if str(output) == string:
                logger.info("Login successful! Already logged in.")
                logger.info("==========================================Completed OC Login==========================================\n\n")
                return
            login_command = ['oc', 'login', f'https://api.{cluster}.cp.fyre.ibm.com:6443', '-u', 'kubeadmin', '-p', f'{password}', '--insecure-skip-tls-verify']
            try:
                login_process = subprocess.Popen(login_command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                login_output, login_error = login_process.communicate(input='y\n', timeout=15)
                if login_output:
                    logger.info(login_output)
                if login_error :
                    logger.error(login_error)
                    logger.critical("Exiting BVT Execution!!")
                    exit()
            except subprocess.TimeoutExpired:
                logger.error("Login process timed out.")
                logger.critical("Exiting BVT Execution!!")
                exit()
            project_change = subprocess.Popen(['oc', 'project', f'{project_name}'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            output, error = project_change.communicate()
            if output :
                logger.info(output)
            if error :
                logger.error(error)
                logger.critical("Exiting BVT Execution!!")
                exit()      
            login_cache = 1
        logger.info("==========================================Completed OC Login==========================================\n\n")
    except Exception as e:
        logger.exception(f"An exception occured while trying to login to the cluster: {e}")
        if file_name:
            raise SanityTestException(f"Failed to login to cluster.") from e 

def get_credentials(project_name):
        """
        Method name: get_credentials
        Author: Nusaiba
        Description: Retrieves and decodes LDAP credentials from OpenShift secrets.
        Parameters: project_name 
        Returns:
            dict: Decoded usernames and passwords.
        """
        config = configparser.ConfigParser()
        config.read('config.ini')
        multildap = config['configurations']['multildap']
        secret_keys = {}
        if multildap.lower()=="true":
            secret_keys = {
                "ldap-bind-secret": [["ldapUsername", "ldapPassword"], ["ldap2Username", "ldap2Password"]],
                "ibm-iam-bindinfo-platform-auth-idp-credentials": [["admin_username", "admin_password"]]
            }
        else:
            secret_keys = {
                "ibm-ban-secret": [["appLoginUsername", "appLoginPassword"]]
            }

        credentials = {}
        for secret, key_pairs in secret_keys.items():
            for user_key, pass_key in key_pairs:
                try:
                    username = fetch_and_decode_secret(secret, user_key, project_name)
                    password = fetch_and_decode_secret(secret, pass_key, project_name)

                    if not username or not password:
                        logger.error(f"Failed to retrieve credentials from {secret} ({user_key}, {pass_key})")
                        raise RuntimeError("Critical error: Missing LDAP credentials. Exiting...")

                    if "cn=" in username.lower():
                        match = re.search(r'(?i)cn=([^,]+)', username)
                        username = match.group(1) if match else exit("Username not found.")

                    credentials[user_key] = username
                    credentials[pass_key] = password
                    logger.info(f"Credentials fetched for {user_key}: {username} and {pass_key}")

                except Exception as e:
                    logger.error(f"Error fetching credentials for {user_key} from {secret}: {e}")
                    raise RuntimeError(f"Critical error: Unable to retrieve credentials for {user_key}. Exiting...")

        return credentials

def fetch_and_decode_secret(secret, key, project_name):
    """
    Method name: fetch_and_decode_secret
    Author: Nusaiba
    Description: Fetches and decodes a secret value from OpenShift.
    Parameters: 
        secret (str): Secret name.
        key (str): Secret key.
        project_name (str) : Namespace
    Returns:
        str: Decoded secret value.
    """
    command = [
        'oc', 'get', 'secret', secret,
        '-n', project_name, '-o', f'jsonpath="{{.data[\'{key}\']}}"'
    ]
    try:
        output = subprocess.run(command, capture_output=True, text=True, check=True).stdout.strip()
        return base64.b64decode(output.strip('"')).decode('utf-8').strip()
    except Exception as e:
        raise RuntimeError(f"Error fetching {key} from {secret}: {e}.")
    
def get_ldap_bind_secret(project_name):
    """
    Method name: get_ldap_bind_secret
    Description: Get the login credentials from the ldap-bind-secret and decode them form base64 format.
    Parameters:
        project_name: The namespace
    Returns:
        username : login username
        pwd : login password
    """
    logger.info("Fetching credentials ...")
    logger.info("Getting ibm-ban secret credentials")
    global cred_cache
    if cred_cache == None :
        pwd_command = [
            'oc', 'get', 'secret', 'ldap-bind-secret',
            '-n', project_name,
            '-o', 'jsonpath="{.data[\'ldapPassword\']}"'
        ]
        uname_command = [
            'oc', 'get', 'secret', 'ldap-bind-secret',
            '-n', project_name,
            '-o', 'jsonpath="{.data[\'ldapUsername\']}"'
        ]
        # Run the 'oc get' command to get the encoded password
        logger.info(f"Running command : {pwd_command}")
        pwd_process = subprocess.Popen(pwd_command, stdout=subprocess.PIPE)
        encoded_pwd, _ = pwd_process.communicate()
        encoded_pwd = encoded_pwd.decode('utf-8').strip()
        # Use base64 module to decode the password
        pwd = base64.b64decode(encoded_pwd).decode('utf-8').strip()
        logger.info("Decoded password.")
        # Run the 'oc get' command to get the encoded username
        logger.info(f"Running command : {uname_command}")
        uname_process = subprocess.Popen(uname_command, stdout=subprocess.PIPE)
        encoded_uname, _ = uname_process.communicate()
        encoded_uname = encoded_uname.decode('utf-8').strip()
        # Use base64 module to decode the username
        uname = base64.b64decode(encoded_uname).decode('utf-8').strip()
        logger.info("Decoded username")
        if "cn" in uname.lower() :
            match = re.search(r'(?i)CN=([^,]+)', uname)
            if match:
                username = match.group(1)
            else:
                logger.error("Username not found.")
                exit()
        else :
            username = uname
        cred_cache = 1
        logger.info(f"Credentials fetched : {username}/{pwd}")
        logger.info("Credentials fetch completed!")
        return username,pwd


if __name__ == "__main__" :
    ocp_login()
    