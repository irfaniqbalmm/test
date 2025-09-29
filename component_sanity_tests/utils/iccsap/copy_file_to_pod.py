import os
import platform
import subprocess
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from utils.logger import logger

def copy_file_to_pod(file, pod, destination_path):
    """
    Method name: copy_file_to_pod
    Author: Anisha Suresh (anisha-suresh@ibm.com)
    Description: Copy the given file to the given destination path in the given pod
    Parameters:
        None
    Returns:
        None
    """
    copy_status = "FAILED"
    try:
        logger.info(f"Copying {file} into {destination_path} directory in {pod} pod")
        try:
            if platform.system() == 'Windows':
                get_pod_command = f'oc get pods | findstr "{pod}" | for /f "tokens=1" %i in (\'more\') do @echo %i'
            else :
                get_pod_command = f'oc get pods | grep "{pod}" | awk \'{{print $1}}\''
            logger.info(f"Executing command: {get_pod_command} to get the {pod} pod name")
            pod_names = subprocess.check_output(get_pod_command, shell=True, text=True).strip()
            pod_name = pod_names.splitlines()[0].strip()
            logger.info(f"{pod} pod name : {pod_name}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get pod name. Error : {e}")
            return

        # Execute the copy command
        copy_command = f'oc cp {file} {pod_name}:{destination_path}'
        logger.info(f"Running command to copy the cmgmt: {copy_command}")
        copy_output = subprocess.run(copy_command, shell=True, check=True)
        logger.info(f"The iccsapTasks.jar file is copied: {copy_output}")
        copy_status = "PASSED"
    except Exception as e:
        raise RuntimeError(f"Failed to copy {file} file to {pod} pod: {e}")
    finally:
        return copy_status

if __name__ == "__main__":
    copy_file_to_pod()
