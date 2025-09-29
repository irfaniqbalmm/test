import subprocess
import configparser
import sys 
import os

def run_script(script_name):
    """
    Method name: run_script
    Author : Nusaiba K K
    Description: Run the main script
    Parameters:  
        script_name : Name of the script to be called
    Returns:  None
    """
    print(f"Running script : {script_name}")
    try:
        result = subprocess.run(["python", script_name], check=True)
        return result.returncode
    except Exception as e:
        print("An exception occured while running main file : ",e)
        return 1

if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read('config.ini')
    user = config.get('configurations','user')
    if user == 'admin':
        print("Executing BVT with admin user.")
        ret_code = run_script("main.py")
        if ret_code == 0:
            print("Execution completed with admin user.")
        else :
            print("FAILED : Execution failed with admin user.")
    elif user == 'non-admin':
        print("Executing BVT with non-admin user.")
        ret_code = run_script("main_non_admin.py")
        if ret_code == 0:
            print("Execution completed with non-admin user.")
        else :
            print("FAILED : Execution failed with non-admin user.")
    else : 
        # Change user to admin first
        config['configurations']['user'] = 'admin'
        # Write changes to the config.ini file
        with open('config.ini', 'w') as configfile:
            config.write(configfile)
        print("Executing BVT with admin user.")
        ret_code = run_script("main.py")
        if ret_code == 0:
            print("Execution completed with admin user.")
            # Change user to non-admin 
            config['configurations']['user'] = 'non-admin'
            # Write changes to the config.ini file
            with open('config.ini','w') as configfile :
                config.write(configfile)
            print("Executing BVT with non-admin user.")
            ret_code = run_script("main_non_admin.py")
            if ret_code == 0:
                print("Execution completed with non-admin user.")
            else :
                print("FAILED : Execution failed with non-admin user.")
        else :
            print("FAILED : Execution failed with admin user.")
        
