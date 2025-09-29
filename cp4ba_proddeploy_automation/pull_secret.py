import subprocess
from utils.logs import *
import sys

log = DeploymentLogs()

def run_oc_command(oc_command):
    """
        Name: run_oc_command
        Author: Dhanesh
        Desc: Common function to run the oc commands
        Parameters:
            oc_command(string): The oc command to run
            log (logging ): The logger object to log
        Returns:
            result: oc command execution output
            False: if the oc command execution fails
        Raises:
            none
    """

    try:
        #Execute oc comands 
        log.logger.info(f'Executing oc command: {oc_command}')
        result = subprocess.run(oc_command, shell = True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        log.logger.info(f"oc command {oc_command} output: \n{result.stdout.decode('utf-8')}")
        print(f"oc command {oc_command} output: \n{result.stdout.decode('utf-8')}")

        #check if the oc command executed successfully
        if result.returncode == 0:

            #verify errors are present in the output
            if result.stderr:
                print(f"Error: {result.stderr.decode('utf-8')}")
                log.logger.info(f"Error: {result.stderr.decode('utf-8')}")
                return False
            else:
                print(f"oc command {oc_command} executed successfully")
                log.logger.info(f"oc command {oc_command} executed successfully")
                return result.stdout.decode('utf-8').strip()
        else:
            print(f"oc command {oc_command} execution was unsuccessful")
            log.logger.info(f"oc command {oc_command} execution was unsuccessful")
            log.logger.info(f"oc command  returned an error: \n{result.stderr.decode('utf-8')}")
            print(f"oc command returned an error: \n{result.stderr.decode('utf-8')}")
            return False
        
    except subprocess.CalledProcessError as e:
        log.logger.info(f"Error: {result.stderr.decode('utf-8')}")
        print(f"Error: {result.stderr.decode('utf-8')}")
        log.logger.info(f"Error: Script returned an error for {oc_command}: {e}")
        print(f"Error: Script returned an error for {oc_command}: {e}")
        return False
    except Exception as e:
        print(f"Error: Unable to execute the oc oc_command {oc_command}: {e}")
        log.logger.info(f"Error: Unable to execute the oc oc_command {oc_command}:  {e}")
        return False

def get_pod_error_status():
    """
        Name: get_pod_error_status
        Author: Dhanesh
        Desc: To return the pods with ImagePullBackOff
        Parameters:
            log (logging ): The logger object to log
        Returns:
            pods: The pods which has the ImagePullBackOff error
        Raises:
            none
    """
    try:
        pods = []
        get_error_pods = "oc get --no-headers=true pods|grep ImagePullBackOff | awk '{print $1}'"
        output = run_oc_command(get_error_pods)
        if not output:
            print('There is no ImagePullBackOff error')
            log.logger.info('There is no ImagePullBackOff error')
        else:
            pods = output.split()
            print(f'The following pods have ImagePullBackOff error: {pods}')
            log.logger.info(f'The following pods have ImagePullBackOff error: {pods}')
            return pods
    except Exception as e:
        print('Error occured getting the pod status to check the pull secret issue: ' + e)
        log.logger.info('Error occured getting the pod status to check the pull secret issue: ' + e)

def check_pull_secret_error():
    """
        Name: check_pull_secret_error
        Author: Dhanesh
        Desc: To check if any pod status is ImagePullBackOff
        Parameters:
            log (logging ): The logger object to log
        Returns:
            none
        Raises:
            ValueError
    """

    error_pods = get_pod_error_status()
    if error_pods:
        for pod in error_pods:
            get_events = f'oc get events | grep -i {pod}'
            events = run_oc_command(get_events)
            if not events:
                print('No events present in the pod')
                log.logger.info('No events present in the pod')
            else:
                if 'Failed to pull image' and 'unable to retrieve auth token: invalid username/password' in events:
                    print(f'pull secret issue in pod {pod}')
                    print(events)
                    log.logger.info(f'pull secret issue in pod {pod}')
                    log.logger.info(events)
                    sys.exit(1)
                else:
                    print(f'ImagePullBackOff error in pod: {pod} \n {events}')
                    log.logger.info(f'ImagePullBackOff error in pod: {pod} \n {events}')
                    sys.exit(1)



if __name__=="__main__":
    check_pull_secret_error()