import os
import requests
import site
import socket
import subprocess
import json 

def find_configobj():
    """
    Function name: find_configobj()
    Desc: find the path of the configobj.py file
    Params: 
        None
    Return:
        path
    """
    site_packages = site.getsitepackages()
 
    #Finding the Path of the configobj.py in site packages  
    for directory in site_packages:
        configobj_path = os.path.join(directory, 'configobj.py')
        if os.path.isfile(configobj_path):
            print(f"configobj.py found in: {configobj_path}")
            return configobj_path
    print("configobj.py not found in any site-packages directory.")
    return None

def modify_configobj():
    """
    Function name: modify_configobj
    Desc: Modify configobj.py file
    Params: 
        None
    Return:
        None
    """
    file_path = find_configobj()
    with open(file_path, 'r') as file:
        lines = file.readlines()

    in_function = False
    
    #Configuring the configobj.py file to our requirements
    with open(file_path, 'w') as file:
        for line in lines:
            if "def _write_line(self, indent_string, entry, this_entry, comment):" in line:
                in_function = True
            if in_function:
                if "self._a_to_u(' = ')," in line:
                    line = line.replace("self._a_to_u(' = '),", "self._a_to_u(\"=\"),")
                if "val = self._decode_element(self._quote(this_entry))" in line:
                    line = line.replace("val = self._decode_element(self._quote(this_entry))", "val = this_entry")
                if line.strip() == "":
                    in_function = False  
            file.write(line)
    print(f"Modified {file_path}")


def fetch_host_shortname():
    """
    Function name: fetch_host_shortname
    Desc: Get the first and last character of the hostname in upper case
    Params: 
        None
    Return:
        first and last character of the hostname in upper case
    """
    try:
        cluster_name =  os.uname().nodename.split('.')[1]
        total_len = len(cluster_name) -1
        short_name = str(cluster_name[0])+str(cluster_name[1])+str(cluster_name[total_len])
        short_name = short_name.upper()
        return short_name
    except Exception as e:
        return 'DT'

def url_check(url):
    """
    Function name: url_check
    Desc: Checking the URL is accesible or not
    Params:
        None
    Return:
        None
    """
    try:
        response = requests.head(url)
        # check the status code
        if response.status_code == 200:
            return True
        else:
            return False
    except requests.ConnectionError as e:
        return False

def svl_machine(cluster_name):
    """
    Function name: svl_machine
    Author: Ann Maria Manuel
    Desc: Checking if the machine belong to SVL or RTP
    Params:
        cluster_name (Name of the cluster )
    Return:
        True/False
    """
    try:
        # Get the path to the current file (i.e., common.py)
        current_file = os.path.abspath(__file__)

        # Go up 2 levels from /utils/common.py to reach /Cp4ba-Automation
        repo_root = os.path.abspath(os.path.join(current_file, "../../.."))

        # Build the full path to cluster.json
        cluster_json_path = os.path.join(repo_root, "CP4BA_Package", "clusters.json")
        #open the clusters.json file and loads its content into a Python dictionary called clusters
        with open(cluster_json_path, "r") as f:
            clusters = json.load(f)
    except Exception as e:
        raise ValueError(f"Error reading cluster.json: {e}")
    
    cluster_info = clusters.get(cluster_name)
    if cluster_info:
        site = cluster_info.get("site", "").lower()
        if site == "svl":
            print(f"Cluster '{cluster_name}' is an SVL cluster.")
            return True
        else:
            print(f"Cluster '{cluster_name}' is an RTP cluster.")
            return False
    else:
        raise ValueError(f"Cluster '{cluster_name}' not found in cluster.json.")

def branch_check(branch):
    """
    Function name: branch_check
    Desc: Checking the branch to enable new features
    Params:
        branch
    Return:
        True/False
    """
    returnstatus = False
    if branch not in ['24.0.0','24.0.0-IF001','24.0.0-IF002','24.0.0-IF003','24.0.0-IF004','24.0.1','24.0.1-IF001']:
        returnstatus = True
    return  returnstatus

def tablespae_branch_check(branch):
    """
    Function name: branch_check
    Desc: Checking the branch to enable new features
    Params:
        branch
    Return:
        True/False
    """
    returnstatus = False
    if branch not in ['24.0.0','24.0.0-IF001','24.0.0-IF002','24.0.0-IF003','24.0.0-IF004','24.0.0-IF005','24.0.1','24.0.1-IF001','24.0.1-IF002']:
        returnstatus = True
    return  returnstatus

def vault_instana_branch_check(branch):
    """
    Function name: vault_branch_check
    Desc: Checking the branch to enable new features vault
    Params:
        branch
    Return:
        True/False
    """
    returnstatus = False
    if branch[:6] in ['25.0.1']:
        returnstatus = True
    return  returnstatus

def run_cmd(cmd, cwd=None, shell=True, return_output=False):
    """
    Function name: run_cmd
    Desc: Running the supplied command
    Params:
        cmd: the command which we need to run
        cwd: current working directory
    Return:
        True/False
    """
    """Run a shell command and print output."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=shell, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False
    else:
        print(result.stdout)
        if return_output:
            count = int(result.stdout.strip())
            if count > 0:
                return True
            else:
                return False
        return True
