import sys
import os
# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import subprocess
import re
from utils.logger import logger

def fetch_oc_version():
    """
    Method name: fetch_oc_version
    Description: Fetch the ocp version.
    Parameters:
        None
    Returns:
        cluster_version :  version of cluster
    """
    try:
        logger.info("Fetching the OCP version ...")
        # Run the 'oc get clusterversion' command
        result = subprocess.run(['oc', 'get', 'clusterversion'], capture_output=True, text=True, check=True)
        # Extract and print the output
        output = result.stdout
        logger.info(f"Cluster version details :\n{output}")
        # Use regex to extract version information from the table
        match = re.search(r"^version\s+(\S+)", output, re.MULTILINE)
        if match:
            cluster_version = match.group(1)
            logger.info(f"Cluster Version: {cluster_version}")
            return cluster_version
        else:
            logger.warning("Cluster Version not found in output.")
            return "None"
    except subprocess.CalledProcessError as e:
        logger.error(f"Error while fetching cluster version: {e}")
    except FileNotFoundError:
        logger.info("The 'oc' command is not found. Please ensure the OpenShift CLI is installed and in your PATH.")

if __name__ == "__main__":
    fetch_oc_version()
    