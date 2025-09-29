import sys
import os
# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import platform

from utils.check_cr_content import *
from utils.logger import logger
from utils.bvt_status import update_status

class JvmCustomOptions:
    def __init__(self):
        pass

    def get_pod_name(self, pod):
        """
        Method name: get_pod_name
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Run oc commad and return the pod name with 'pod' in it
        Parameters:
            pod (str) : part of name of pod 
        Returns:
            pod_name (str) : entire pod name
        Raises :
            CalledProcessError: If the command fails to run
        """
        try:
            if platform.system() == 'Windows':
                get_pod_command = f'oc get pods | findstr "{pod}" | for /f "tokens=1" %i in (\'more\') do @echo %i'
            else :
                get_pod_command = f'oc get pods | grep "{pod}" | awk \'{{print $1}}\''
            pod_names = subprocess.check_output(get_pod_command, shell=True, text=True).strip()
            pod_name = pod_names.splitlines()[0].strip()
            logger.info(f"Component pod name : {pod_name}")
            return pod_name
        except subprocess.CalledProcessError as e:
            logger.error('Failed to get pod name.')
            logger.error(f"An exception occured while getting pod name : {e}")
            return
        
    def run_command(self, pod_name, command):
        """
        Method name: run_command
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Run oc commad and return the jvm customise options output
        Parameters:
            pod (str) : name of pod in which the command has to be run
            command (str) : command to be run
        Returns:
            jvm_options_output : jvm customized options
        Raises :
            e: Exception
        """
        try :
            oc_command = f'oc exec {pod_name} -- {command}' 
            logger.info(f"Executing the command : {oc_command}")
            jvm_custom_options = subprocess.Popen(oc_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            jvm_options_output, jvm_options_error = jvm_custom_options.communicate()
            if jvm_options_output:
                logger.info(f'JVM options fetched : {jvm_options_output}')
            else:
                logger.error(f'Error getting jvm options : {jvm_options_error}')
            return jvm_options_output
        except Exception as e:
            logger.error(f"An exception occured during executing the command : {e}")

    def verify_jvm_custom_options(self):
        """
        Method name: verify_jvm_custom_options
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: BVT verification of jvm custom options for different components
        Parameters:
            keyword : content to be checked
        Returns:
            keyword value / False
        """
        jvm_options_status = "PASSED"
        logger.info("Getting the CR content.")
        file_content = get_cr_data()
        logger.info("Loading the cr data")
        cr_data = yaml.safe_load(file_content)
        components = ["CPE","CMIS","GRAPHQL","TM","ICN","IER"]
        for component in components:
            logger.info(f"Fetching the JVM options for the component: {component}")
            component_jvm_options = get_jvm_customize_options(component, cr_data)
            if component_jvm_options:
                component_pod_name = self.get_pod_name(f"{component.lower()}-deploy")
                env_jvm_options = self.run_command(component_pod_name, 'sh -c "echo $JVM_CUSTOMIZE_OPTIONS"')
                file_jvm_options = self.run_command(component_pod_name, "cat jvm.options")
                logger.info(f"Checking if the jvm options from CR are presnt in the pod")
                if str(component_jvm_options) in str(env_jvm_options):
                    logger.info(f"JVM customized options present in the env variable.")
                    if str(component_jvm_options) in str(file_jvm_options):
                        logger.info(f"JVM customized options present in the jvm.options file.")
                    else :
                        logger.error(f"JVM customized options NOT present in the jvm.options file.")
                        jvm_options_status = "FAILED"
                else :
                    logger.error(f"JVM customized options NOT present in the env variable.")
                    jvm_options_status = "FAILED"
            else : 
                logger.debug(f"JVM customized options not present for the component {component} in the CR.")
        update_status("JVM_Custom_Options",jvm_options_status)

if __name__ == "__main__" :
    jvm_custom_options = JvmCustomOptions()
    jvm_custom_options.verify_jvm_custom_options()