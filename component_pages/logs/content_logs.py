import sys
import os
import platform
import subprocess

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from utils.logger import logger

def get_content_logs(logs_path, project_name) :
    """
    Method name: get_content_logs
    Description: Get the logs from the content-operator pod
    Parameters:
        logs_path : Path to downloaded log files
        project_name : Namespace of the project
    Returns:
        None
    """
    location = f"/tmp/ansible-operator/runner/icp4a.ibm.com/v1/Content/{project_name}/content/artifacts/"
    logger.info(f"Expected location of operator logs : {location}")
    if platform.system() != 'Windows' :
        # Get pod name
        pod_name = None
        logger.info("Fetching operator pod name ...")
        pod_name = os.popen("oc get pods | grep content-operator | awk 'NR==1{print $1}'").read().strip()
        if pod_name is None:
            logger.error("Error: Could not find content-operator pod.")
            logger.critical("Logs check failed!")
            return
        logger.info(f"Content-Operator pod name is : {pod_name}")
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
            os.system(f"oc cp {pod_name}:'{location}{latest_file}/stdout' {logs_path}/content_operator_log_latest.txt")
            logger.info(f"Log file download complete: /{logs_path}/content_operator_log_latest.txt")
    else :
        # Get pod name
        logger.info("Fetching operator pod name ...")
        result = subprocess.run(["oc", "get", "pods"], capture_output=True, text=True)
        pod_name = None
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            for line in lines:
                if "content-operator" in line:
                    pod_name = line.split()[0]
                    break
        if pod_name is None:
            logger.error("Error: Could not find content-operator pod.")
            logger.critical("Logs check failed!")
            return
        logger.info(f"Content-Operator pod name is : {pod_name}")
        logger.info("Downloading the latest operator log file ...")
        result = subprocess.run(["oc", "exec", pod_name, "--", "bash", "-c", f"ls -t {location}"], capture_output=True, text=True)
        if result.returncode == 0:
            latest_file = f"{location}latest/stdout"
            stdout_result = subprocess.run(["oc", "exec", pod_name, "--", "cat", latest_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout_text = stdout_result.stdout.decode("utf-8")
            if stdout_result.returncode == 0:
                with open(f"{logs_path}/content_operator_log_latest.txt", "w", encoding="utf-8") as file:
                    file.write(stdout_text)
                logger.info(f"File download complete: {logs_path}/content_operator_log_latest.txt")
            else:
                logger.error("Failed to get latest file content.")
                logger.critical("Logs check failed!")
        else:
            logger.error("Failed to get latest file")
            logger.critical("Logs check failed!")

if __name__ == "__main__" :
    get_content_logs()
    