import sys
import os
# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import subprocess
import platform
import re
from tomlkit import parse
from utils.logger import logger

def create_network_policies() :
    """
    Method name: create_network_policies
    Description: Creates the network policies for CMOD & CM8 connections.
    Parameters:
        None
    Returns:
        None
    """
    with open("./inputs/config.toml","r") as file :
        config = parse(file.read())

    namespace = config['configurations']['project_name']

    logger.info("==========================================Starting creation of network policies==========================================")
    try:
        logger.info("Fetching navigator pod name...")
        if platform.system() == 'Windows':
            get_pod_command = 'oc get pods | findstr "navigator-deploy" | for /f "tokens=1" %i in (\'more\') do @echo %i'
        else :
            get_pod_command = f'oc get pods | grep "navigator-deploy" | awk \'{{print $1}}\''
        pod_names = subprocess.check_output(get_pod_command, shell=True, text=True).strip()
        pod_name = pod_names.splitlines()[0]
        logger.info(f"Navigator pod name fetched : {pod_name}")
        match = re.match(r'^([a-z0-9-]+)-[a-z0-9]+-[a-z0-9]+$', pod_name)
        if match:
            pod_base_name = match.group(1)
        else:
            pod_base_name = ""
    except subprocess.CalledProcessError as e:
        logger.error('Failed to get pod name.')
        logger.error(f"An exception occured during fetching the navigator pod name : {e}")

    # CMOD network policy template
    cmod_network_policy_yaml = f"""
    kind: NetworkPolicy
    apiVersion: networking.k8s.io/v1
    metadata:
        name: cmod-network-policy
        namespace: {namespace}
    spec:
        podSelector:
            matchLabels:
                app.kubernetes.io/instance: {pod_base_name}
        egress:
            - to:
                - ipBlock:
                    cidr: 9.30.211.62/0
        policyTypes:
            - Egress
    """
    # Save the YAML to a file
    logger.info("Saving CMOD YAML to file")
    with open("./component_pages/navigator/network_policies/cmod-network-policy.yaml", "w") as f:
        f.write(cmod_network_policy_yaml)

    # Apply the network policy using oc command
    try:
        subprocess.run(["oc", "apply", "-f", "./component_pages/navigator/network_policies/cmod-network-policy.yaml"], check=True)
        logger.info("CMOD network policy applied successfully")
    except subprocess.CalledProcessError as e:
        logger.error("An exception occured during creation CMOD network policy.")
        logger.error(f"Failed to apply network policy:", {e})

    # Describe the network policy
    try:
        subprocess.run(["oc", "describe", "networkpolicy", "cmod-network-policy", "-n", namespace], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to describe network policy:", {e})

     # CM8 network policy template
    cm8_network_policy_yaml = f"""
    kind: NetworkPolicy
    apiVersion: networking.k8s.io/v1
    metadata:
        name: cm8-network-policy
        namespace: {namespace}
    spec:
        podSelector:
            matchLabels:
                app.kubernetes.io/instance: {pod_base_name}
        egress:
            - to:
                - ipBlock:
                    cidr: 9.30.45.218/0
        policyTypes:
            - Egress
    """
    # Save the YAML to a file
    logger.info("Saving CM8 YAML to file")
    with open("./component_pages/navigator/network_policies/cm8-network-policy.yaml", "w") as f:
        f.write(cm8_network_policy_yaml)

    # Apply the network policy 
    try:
        subprocess.run(["oc", "apply", "-f", "./component_pages/navigator/network_policies/cm8-network-policy.yaml"], check=True)
        logger.info("CM8 network policy applied successfully")
    except subprocess.CalledProcessError as e:
        logger.error("An exception occured during creation CM8 network policy.")
        logger.error(f"Failed to apply network policy:", {e})

    # Describe the network policy
    try:
        subprocess.run(["oc", "describe", "networkpolicy", "cm8-network-policy", "-n", namespace], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to describe network policy:", {e})

    logger.info("==========================================Completed creation of network policies==========================================\n\n")

if __name__ == "__main__" :
    create_network_policies()
