import sys
import os
import platform
import subprocess
from termcolor import colored
from tomlkit import parse
from pathlib import Path
# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from utils.logger import logger

def get_bai_operator_logs():
    """
    Method name: get_bai_operator_logs
    Description: Get the logs from the bai operator pod
    Parameters:
        None
    Returns:
        None
    """
    with open("./BAI_BVT/resources/config.toml","r") as file :
        config = parse(file.read())
    project_name = config['configurations']['project_name']
    logs_path = Path(config['paths']['download_path'],'logs')

    if os.path.exists(logs_path):
        logger.info("Logs folder already exists.")
    else :
        logger.info("Creating logs folder.")
        os.mkdir(logs_path)

    location = f"/tmp/ansible-operator/runner/bai.ibm.com/v1/InsightsEngine/{project_name}/bai/artifacts/"
    logger.info(f"Expected location of operator logs : {location}")
    if platform.system() != 'Windows' :
        # Get pod name
        pod_name = None
        logger.info("Fetching operator pod name ...")
        pod_name = os.popen("oc get pods | grep bai-insights-engine-operator | awk 'NR==1{print $1}'").read().strip()
        if pod_name is None:
            logger.error("Error: Could not find bai-operator pod.")
            logger.critical("Logs check failed!")
            return
        logger.info(f"bai-Operator pod name is : {pod_name}")
        # Check if the directory exists
        logger.info("Check if expected directory for logs is present in operator pod ...")
        if os.system(f"oc exec {pod_name} -- bash -c '[ -d \"{location}\" ]'") != 0:
            logger.error("Directory not found in the pod.")
            logger.critical("Logs check failed!")
            return
        else:
            logger.info("Directory found in the pod.")
            logger.info("Downloading the latest operator log file ...")
            latest_file = os.popen(f"oc exec {pod_name} -- bash -c \"ls -t \\\"{location}\\\" | head -1\"").read().strip()
            os.system(f"oc cp {pod_name}:'{location}{latest_file}/stdout' {logs_path}/bai_operator_log_latest.txt")
            logger.info(f"Log file download complete: /{logs_path}/bai_operator_log_latest.txt")
    else :
        # Get pod name
        logger.info("Fetching bai operator pod name ...")
        result = subprocess.run(["oc", "get", "pods"], capture_output=True, text=True)
        pod_name = None
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            for line in lines:
                if "bai-insights-engine-operator" in line:
                    pod_name = line.split()[0]
                    break
        if pod_name is None:
            logger.error("Error: Could not find content-operator pod.")
            logger.critical("Logs check failed!")
            return
        logger.info(f"bai-Operator pod name is : {pod_name}")
        logger.info("Downloading the latest operator log file ...")
        result = subprocess.run(["oc", "exec", pod_name, "--", "bash", "-c", f"ls -t {location}"], capture_output=True, text=True)
        if result.returncode == 0:
            latest_file = f"{location}latest/stdout"
            stdout_result = subprocess.run(["oc", "exec", pod_name, "--", "cat", latest_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout_text = stdout_result.stdout.decode("utf-8")
            if stdout_result.returncode == 0:
                with open(f"{logs_path}/bai_operator_log_latest.txt", "w", encoding="utf-8") as file:
                    file.write(stdout_text)
                logger.info(f"File download complete: {logs_path}/bai_operator_log_latest.txt")
            else:
                logger.error("Failed to get latest file content.")
                logger.critical("Logs check failed!")
        else:
            logger.error("Failed to get latest file")
            logger.critical("Logs check failed!")

def check_log_errors(file_path):
    """
    Method name: check_errors
    Description: Check if any errors are present in the operator logs using the keyword "FATAL!"
    Parameters:
        file_path : Path to logs
    Returns:
        True / False
    """
    logger.info("Checking if any errors are present in the operator logs using the keyword 'FATAL!'")
    try:
        logger.info("Opening operator log file.")
        with open(file_path, 'r',encoding="utf-8") as file:
            for line in file:
                if "FAILED!" in line or "fatal" in line:
                    logger.warning("Errors present in operator logs!!")
                    return True
        logger.info("No errors present in operator logs!!")
        return False
    except FileNotFoundError as e:
        logger.debug(f"An exception thrown file checking errors : {e}")
        logger.warning(f"Error: File '{file_path}' not found. Ignoring error.")
        return False

if __name__ == "__main__" :
    get_bai_operator_logs()
    