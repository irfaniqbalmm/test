import subprocess
from utils import bvt_status
import base64

missing_list = []
issue_list = []

def run_oc_command(oc_command, log):
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


def verify_results(oc_command, expected_results, log):
    """
        Name: verify_results
        Author: Dhanesh
        Desc: To verify the oc commands returns the correct output by checking if the expected results is present in the oc command output
        Parameters:
            oc_command(string): The oc command to run
            expected_results(list): list of expected results to verify in the command output 
            log (logging ): The logger object to log
        Returns:
            Dictionary: {oc_command: missing_values}
        Raises:
            none
    """

    actual_result = run_oc_command(oc_command, log)
    # Verify result only if the command execution is successful
    if actual_result:
        missing_values =  [value.strip() for value in expected_results if value.strip() not in actual_result]

        #Check if any of the exepected values are missing
        if missing_values:
            print(f'The following values are not present in the output: \n {missing_values}')
            log.logger.info(f'The following values are not present in the output: \n {missing_values}')
            return {oc_command: missing_values}
        else:
            print(f'All the expected values: {expected_results} are present in the OC command output')
            log.logger.info(f'All the expected values: {expected_results} are present in the OC command output')
            return True
    else:
        return False


def verify_result(oc_command, expected_result, log):
    """
        Name: verify_results
        Author: Dhanesh
        Desc: To verify the oc commands returns the correct output by comparing the exact value
        Parameters:
            oc_command(string): The oc command to run
            expected_result(string): The value to verify
            log (logging ): The logger object to log
        Returns:
            Dictionary: {oc_command: value}
        Raises:
            none
    """

    actual_result = run_oc_command(oc_command, log)
    if ('data.admin_username' in oc_command or 'data.admin_password' in oc_command or 'data.appLoginUsername' in oc_command or 'data.appLoginPassword' in oc_command):
       actual_result = base64.b64decode(actual_result).decode('utf-8').strip()
    if actual_result != expected_result:
        print(f'The actual result {actual_result} and expected result {expected_result} are not matching')
        log.logger.info(f'The actual result {actual_result} and expected result {expected_result} are not matching')
        return {oc_command: actual_result}
    else:
        print(f'The actual result {actual_result} and expected result {expected_result} are matching')
        log.logger.info(f'The actual result {actual_result} and expected result {expected_result} are matching')
        return True


def verify_partial_result(oc_command, expected_result, log):
    """
        Name: verify_secret
        Author: Dhanesh
        Desc: To verify the expected results are present in the command output
        Parameters:
            none
        Returns:
            none
        Raises:
            valueError
    """
    
    log.logger.info('---------------------------------------------------------------------------------------------------------------------------')
    print('---------------------------------------------------------------------------------------------------------------------------')
    output = verify_results(oc_command, expected_result, log)
    if isinstance(output, dict):
        print(f'oc command {oc_command} failed')
        log.logger.info(f'oc command {oc_command} failed')
        missing_list.append(output)
    elif output is False:
        print(f'oc command {oc_command} failed')
        log.logger.info(f'oc command {oc_command} failed')
        issue_list.append(oc_command)
    elif output is True:
        print(f'oc command {oc_command} verified sucessfully')
        log.logger.info(f'oc command {oc_command} verified sucessfully')
    else:
        raise ValueError(f'Unknown value {output}')

def verify_exact_result(oc_command, expected_result, log):
    """
        Name: verify_ibm_fncm_secret_username
        Author: Dhanesh
        Desc: To verify the actual and expected results are matching
        Parameters:
            none
        Returns:
            none
        Raises:
            valueError
    """

    log.logger.info('---------------------------------------------------------------------------------------------------------------------------')
    print('---------------------------------------------------------------------------------------------------------------------------')
    output = verify_result(oc_command, expected_result, log)
    print(output)
    if isinstance(output, dict):
        print(f'oc command {oc_command} failed')
        log.logger.info(f'oc command {oc_command} failed')
        missing_list.append(output)
    elif output is False:
        print(f'oc command {oc_command} failed')
        log.logger.info(f'oc command {oc_command} failed')
        issue_list.append(oc_command)
    elif output is True:
        print(f'oc command {oc_command} verified sucessfully')
        log.logger.info(f'oc command {oc_command} verified sucessfully')
    else:
        raise ValueError(f'Unknown value {output}')

def validate(log):
    """
        Name: validate
        Author: Dhanesh
        Desc: To validate the failures
        Parameters:
            none
        Returns:
            none
        Raises:
            valueError
    """
    is_failed = False
    if missing_list:
        log.logger.info(f'The following expected results are missing in the OC commands:  {missing_list}')
        print(f'The following expected results are missing in the OC commands:  {missing_list}')
        is_failed = True
    if issue_list:
        log.logger.info(f'The following OC commands failed:  {issue_list}')
        print(f'The following OC commands failed:  {issue_list}')
        is_failed = True
    if is_failed :
        bvt_status.update_status("OC_Automations","FAILED")
    else :
        bvt_status.update_status("OC_Automations","PASSED")
    return is_failed

    