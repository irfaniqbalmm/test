#!/usr/bin/env python3

import sys
import logging
import os
import json
import subprocess
import shutil
from playwright.sync_api import sync_playwright

# Configuration
BASE_DIR = "/opt/Cp4ba-Automation"
LOG_FILE = "/opt/Cp4ba-Automation/cp4ba_proddeploy_automation/logs/formview_prod_deploy.log"
CLUSTERS_FILE = os.path.join(BASE_DIR, "CP4BA_Package", "clusters.json")

# Setup logging - match original format exactly
LOG_DIR = "/opt/Cp4ba-Automation/cp4ba_proddeploy_automation/logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Reset any previous handlers to match original
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

logging.basicConfig(
    filename=LOG_FILE,
    filemode="a",
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Add project paths
project_paths = [
    BASE_DIR,
    os.path.join(BASE_DIR, "cp4ba_proddeploy_automation"),
    os.path.join(BASE_DIR, "cp4ba_proddeploy_automation", "utils")
]
for path in project_paths:
    sys.path.insert(0, path)

# Import project modules
from cp4ba_proddeploy_automation.utils.common import modify_configobj, svl_machine
from cp4ba_proddeploy_automation.utils.utils_class import *
from cp4ba_proddeploy_automation.utils.logs import *
from cp4ba_proddeploy_automation.db_operations import *
from cp4ba_proddeploy_automation.pull_secret import *
from formview_prod.formview_util import *
from formview_prod.formview_locators import *
from formview_prod.formview_play import *
from formview_prod.formview_data import *

# Load cluster configuration
with open(CLUSTERS_FILE, "r") as f:
    clusters = json.load(f)

# Original logging setup
log = DeploymentLogs(logname="formview_prod")
logger = log.logger


def run_command_safe(cmd, logger_obj):
    """
    Safe command runner with proper error handling
    """
    try:
        logger_obj.info(f"Executing command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        if result.stdout:
            logger_obj.debug(f"Command stdout: {result.stdout}")
        if result.stderr:
            logger_obj.warning(f"Command stderr: {result.stderr}")
        logger_obj.info(f"Command completed successfully with return code: {result.returncode}")
        return True
    except subprocess.CalledProcessError as e:
        logger_obj.error(f"Command failed: {' '.join(cmd)}")
        logger_obj.error(f"Return code: {e.returncode}")
        if e.stdout:
            logger_obj.error(f"Stdout: {e.stdout}")
        if e.stderr:
            logger_obj.error(f"Stderr: {e.stderr}")
        return False
    except FileNotFoundError as e:
        logger_obj.error(f"Command not found: {' '.join(cmd)}")
        logger_obj.error(f"Error: {str(e)}")
        return False
    except Exception as e:
        logger_obj.error(f"Unexpected error running command: {' '.join(cmd)}")
        logger_obj.error(f"Error: {str(e)}")
        return False


def pathupdate_dataconfig_fixed(deploy_obj):
    """
    Fixed version of pathupdate_dataconfig function
    This bypasses the broken version in utils_class.py
    """
    try:
        log.logger.info("Starting FIXED pathupdate_dataconfig function")
        log.logger.info(f"Branch: {deploy_obj.branch}, Type: {type(deploy_obj.branch)}")
        
        # Check branch condition
        if deploy_obj.branch == '24.0.0':
            log.logger.info("Branch is 24.0.0, skipping path updates")
            return True
        
        log.logger.info(f"Branch is not 24.0.0, proceeding with path updates")
        
        # Update project name if separation duty is enabled
        project_name = deploy_obj.project_name
        if hasattr(deploy_obj, 'separation_duty_on') and deploy_obj.separation_duty_on == 'yes':
            if hasattr(deploy_obj, 'operand_namespace_suffix'):
                original_project_name = project_name
                project_name = str(project_name) + str(deploy_obj.operand_namespace_suffix)
                log.logger.info(f"Updated project name from '{original_project_name}' to '{project_name}' due to separation duty")
            else:
                log.logger.warning("separation_duty_on is 'yes' but operand_namespace_suffix is not set")
        
        # Validate data.config file exists
        current_dir = os.getcwd()
        dataconfig_path = os.path.join(current_dir, 'config', 'data.config')
        
        log.logger.info(f"Current directory: {current_dir}")
        log.logger.info(f"Data config path: {dataconfig_path}")
        
        if not os.path.exists(dataconfig_path):
            log.logger.error(f"data.config file not found at: {dataconfig_path}")
            return False
        
        if not os.access(dataconfig_path, os.R_OK | os.W_OK):
            log.logger.error(f"data.config file is not readable/writable: {dataconfig_path}")
            return False
            
        log.logger.info(f"data.config file validated successfully")
        
        # Create backup of data.config
        backup_path = dataconfig_path + ".backup"
        try:
            shutil.copy2(dataconfig_path, backup_path)
            log.logger.info(f"Created backup at: {backup_path}")
        except Exception as e:
            log.logger.warning(f"Failed to create backup: {e}")
        
        # Helper function to validate and perform sed replacement
        def perform_sed_replacement(replace_from, replace_with, target_path, description):
            log.logger.info(f"=== {description} ===")
            log.logger.info(f"Target file: {target_path}")
            log.logger.info(f"Replace FROM: '{replace_from}'")
            log.logger.info(f"Replace WITH: '{replace_with}'")
            
            # Check if target file exists
            if not os.path.exists(target_path):
                log.logger.error(f"Target file does not exist: {target_path}")
                return False
            
            # Check if pattern exists in file before replacement
            try:
                with open(target_path, 'r') as f:
                    content = f.read()
                
                pattern_count = content.count(replace_from)
                log.logger.info(f"Pattern '{replace_from}' found {pattern_count} times in {target_path}")
                
                if pattern_count == 0:
                    log.logger.warning(f"Pattern '{replace_from}' not found in {target_path} - skipping replacement")
                    return True  # Not an error, just no match
                    
            except Exception as e:
                log.logger.error(f"Error reading file {target_path}: {e}")
                return False
            
            # Perform sed replacement
            cmd = ["sed", "-i", f"s;{replace_from};{replace_with};g", target_path]
            result = run_command_safe(cmd, log.logger)
            
            if result:
                log.logger.info(f"✓ Successfully completed {description}")
            else:
                log.logger.error(f"✗ Failed {description}")
            
            return result
        
        # 1. Replace the property file folder path
        if not perform_sed_replacement(
            'cp4ba-prerequisites/propertyfile',
            f'cp4ba-prerequisites/project/{project_name}/propertyfile',
            dataconfig_path,
            "property file folder path replacement"
        ):
            return False

        # 2. Replace the db file path
        if not perform_sed_replacement(
            'scripts/cp4ba-prerequisites/dbscript',
            f'scripts/cp4ba-prerequisites/project/{project_name}/dbscript',
            dataconfig_path,
            "db file path replacement"
        ):
            return False

        # 3. Replace the prereq folder path
        if not perform_sed_replacement(
            'PREREQ_FOLDER=/opt/ibm-cp-automation/scripts/cp4ba-prerequisites/',
            f'PREREQ_FOLDER=/opt/ibm-cp-automation/scripts/cp4ba-prerequisites/project/{project_name}/',
            dataconfig_path,
            "prereq folder path replacement"
        ):
            return False

        # 4. Generated CR path update
        if not perform_sed_replacement(
            'GENERATED_CR=/opt/ibm-cp-automation/scripts/generated-cr/',
            f'GENERATED_CR=/opt/ibm-cp-automation/scripts/generated-cr/project/{project_name}/',
            dataconfig_path,
            "generated CR path replacement"
        ):
            return False

        # 5. Handle postgres-specific script update
        if hasattr(deploy_obj, 'db') and deploy_obj.db == 'postgres':
            scriptpath = os.path.join(current_dir, 'certs/scripts/ibm-cp4ba-db-ssl-cert-secret-for-postgres.sh')
            log.logger.info(f"Database is postgres, checking script: {scriptpath}")
            
            if os.path.exists(scriptpath):
                if not perform_sed_replacement(
                    'scripts/cp4ba-prerequisites/propertyfile',
                    f'scripts/cp4ba-prerequisites/project/{project_name}/propertyfile',
                    scriptpath,
                    "postgres script path replacement"
                ):
                    return False
            else:
                log.logger.warning(f"Postgres script not found: {scriptpath} - skipping")

        # 6. Update external certificate path
        if not perform_sed_replacement(
            'cp4ba-prerequisites/propertyfile/cert/cp4ba_tls_issuer',
            f'cp4ba-prerequisites/project/{project_name}/propertyfile/cert/cp4ba_tls_issuer',
            dataconfig_path,
            "external certificate path replacement"
        ):
            return False

        log.logger.info(f"✓ Successfully completed FIXED pathupdate_dataconfig with branch '{deploy_obj.branch}' and project name '{project_name}'")
        return True
        
    except Exception as e:
        log.logger.error(f"✗ Exception in FIXED pathupdate_dataconfig: {str(e)}")
        log.logger.error(f"Exception type: {type(e).__name__}")
        import traceback
        log.logger.error(f"Traceback: {traceback.format_exc()}")
        return False


def test_pathupdate_function(deploy_obj):
    """
    Test function to verify our pathupdate fix works
    """
    log.logger.info("=" * 60)
    log.logger.info("TESTING PATHUPDATE FUNCTION")
    log.logger.info("=" * 60)
    
    # Test our fixed function
    result = pathupdate_dataconfig_fixed(deploy_obj)
    
    if result:
        log.logger.info("✓ PATHUPDATE TEST PASSED!")
        log.logger.info("The pathupdate_dataconfig_fixed function completed successfully")
    else:
        log.logger.error("✗ PATHUPDATE TEST FAILED!")
        log.logger.error("Check the logs above for detailed error information")
    
    log.logger.info("=" * 60)
    return result


def setup_openshift_cluster(deploy, project):
    """Setup OpenShift cluster with required projects and bindings"""
    log.logger.info("Setting up OpenShift cluster")
    
    # Define cluster role bindings to check and potentially delete
    bindings_to_check = [
        'dbbinding',
        'user-aggregate-olm-view'
    ]
    
    # Clean up existing resources only if they exist
    for binding in bindings_to_check:
        log.logger.info(f"Checking and cleaning up clusterrolebinding: {binding}")
        
        # Use oc delete with --ignore-not-found flag - this will delete if exists, ignore if not
        delete_cmd = ["oc", "delete", "clusterrolebinding", binding, "--ignore-not-found=true"]
        run_command(delete_cmd)
        log.logger.info(f"Cleanup completed for clusterrolebinding: {binding}")
    
    # Create cluster role bindings
    try:
        run_command(["oc", "create", "clusterrolebinding", 'dbbinding', "--clusterrole=admin", "--user", 'dbauser'])
        log.logger.info('clusterrolebinding dbbinding created successfully')
    except Exception as e:
        log.logger.error(f'Failed to create clusterrolebinding dbbinding: {e}')
        raise
    
    try:
        run_command(["oc", "create", "clusterrolebinding", "user-aggregate-olm-view", "--clusterrole=aggregate-olm-view", "--user", 'dbauser'])
        log.logger.info('clusterrolebinding user-aggregate-olm-view created successfully')
    except Exception as e:
        log.logger.error(f'Failed to create clusterrolebinding user-aggregate-olm-view: {e}')
        raise
    
    # Create projects
    projects = ["ibm-cert-manager", "ibm-licensing", project]
    for proj in projects:
        run_command(["oc", "new-project", proj])
        log.logger.info(f'new-project {proj} created')
    
    # Configure operator group and catalog source
    update_operator_group_yaml(operator_group_yaml_path, project)
    log.logger.info(f'operator_group_yaml {operator_group_yaml_path} updated')
    
    run_command(["oc", "create", "-n", project, "-f", operator_group_yaml_path])
    log.logger.info(f'oc create -n {project} -f {operator_group_yaml_path} success')
    
    run_command(["oc", "project", project])
    log.logger.info(f'{project} selected')
    
    run_command(["oc", "apply", "-f", catalogue_source_yaml_path])
    log.logger.info(f'catalogue_source_yaml {catalogue_source_yaml_path} applied')
    
    # Create and apply config map
    create_configmap_yaml(configmap_yaml_path, project)
    log.logger.info(f'configmap_yaml {configmap_yaml_path} created')
    
    run_command(["oc", "apply", "-f", configmap_yaml_path])
    log.logger.info(f'configmap_yaml {configmap_yaml_path} applied')
    
    run_command(["oc", "apply", "-f", operator_group_yaml_path])
    log.logger.info(f'operator_group_yaml {operator_group_yaml_path} applied')


def login_to_console(page, cluster_name, kube_pass):
    """Login to OpenShift console"""
    log.logger.info("Logging into OpenShift console")
    
    page.goto(f"https://console-openshift-console.apps.{cluster_name}.cp.fyre.ibm.com")
    page.wait_for_load_state("networkidle")
    wait_for_seconds()
    log.logger.info('OCP console opened')
    
    # Handle SSL warnings
    click_if_found(page, Locators.advanced)
    log.logger.info('Advanced clicked')
    click_if_found(page, Locators.proceed)
    log.logger.info('Proceed clicked')
    
    # Login
    wait_for_locator_visible(page, Locators.kubeadmin, timeout=30000)
    safe_click(page, Locators.kubeadmin)
    log.logger.info('kubeadmin clicked')
    
    safe_fill(page, Locators.input_username, "kubeadmin")
    log.logger.info('kubeadmin username filled')
    
    safe_fill(page, Locators.input_password, kube_pass)
    log.logger.info('kubeadmin password filled')
    
    safe_click(page, Locators.login)
    log.logger.info('login clicked')
    
    wait_and_reload(page)
    log.logger.info('waiting for operator button to be visible')
    wait_for_locator_visible(page, Locators.operators, timeout=30000)


def install_operators(page):
    """Install required operators"""
    operators = [
        ("ibm_cert_manager", install_ibm_cert_manager_Operator),
        ("ibm_licensing", install_ibm_licensing_Operator),
        ("ibm_cp4ba_filenet_content_manager", install_ibm_cp4ba_filenet_content_manager)
    ]
    
    for name, install_func in operators:
        log.logger.info(f'installing {name} Operator')
        install_func(page)
        wait_and_reload(page)
    
    log.logger.info('waiting for operator installations to complete')
    wait_for_installation(page)
    
    # Check errors in pods
    log.logger.info('Verify pod status')
    check_pull_secret_error()


def configure_database(deploy, db, external_db, tablespace_option):
    """Configure database operations"""
    if external_db == 'yes':
        log.logger.info('Creating sql statement for BTS/IM/ZEN.')
        create_sql_status = deploy.create_sql()
        if not create_sql_status:
            log.logger.error('Creating sql statement for BTS/IM/ZEN failed.')
            raise Exception("Creating sql statement for BTS/IM/ZEN failed.")
        else:
            # Db deletion and creation for the external postgres to store metastore
            log.logger.info('Running the Db Operations for the external postgres to store metastore.')
            DbOperations('postgres_metastore', tablespace_option)
    
    # Db deletion and creation
    log.logger.info('Running the Db Operations.')
    DbOperations(db, tablespace_option)


def configure_ldap_and_db(page, ldap, db):
    """Configure LDAP and database settings"""
    # LDAP Configuration
    if ldap.upper() == "MSAD":
        log.logger.info('filling LDAP configuration with MSAD')
        create_content_LDAP_Configuration_MSAD(page)
    elif ldap.upper() == "TDS":
        log.logger.info('filling LDAP configuration with TDS')
        create_content_LDAP_Configuration_TDS(page)
    else:
        log.logger.warning(f"Unknown LDAP type '{ldap}' — skipping LDAP configuration")
    
    # Database Configuration
    if db.upper() == "MSSQL":
        log.logger.info('filling DB configuration with MSSQL')
        create_content_DB_Configuration_MSSQL(page)
    elif db.upper() == "ORACLE":
        log.logger.info('filling DB configuration with ORACLE')
        create_content_DB_Configuration_ORACLE(page)
    elif db.upper() == "POSTGRES":
        log.logger.info('filling DB configuration with PostgressSQL')
        create_content_DB_Configuration_PostgressSQL(page)
    elif db.upper() == "DB2":
        log.logger.info('filling DB configuration with DB2')
        create_content_DB_Configuration_DB2(page)
    else:
        log.logger.warning(f"Unknown DB type '{db}' — skipping DB configuration")


def main():
    """Main deployment function"""
    browser = None
    try:
        log.logger.info("Starting FormView production deployment")
        
        # Parse configuration
        config_dict = json.loads(sys.argv[1])
        
        # Extract configuration values with defaults
        db = config_dict.get('dbname', '')
        ldap = config_dict.get('ldapname', '')
        project = config_dict.get('project', 'cp22')
        branch = config_dict.get('branch', 'CP4BA-24.0.1-IF001')
        stage_prod = config_dict.get('stage_prod', 'dev')
        cluster_name = config_dict.get('cluster_name', 'india')
        cluster_pass = config_dict.get('cluster_pass', '')
        fips = config_dict.get('fips', 'no').lower()
        external_db = config_dict.get('external_db', 'no').lower()
        extcrt = config_dict.get('extcrt', 'no').lower()
        git_branch = config_dict.get('git_branch', 'master')
        tablespace_option = config_dict.get('tablespace_option', 'yes')
        egress = config_dict.get('egress', 'No')
        component_names = config_dict.get('component_names', '')
        fisma = config_dict.get('fisma', 'NO')
        
        KUBE_PASS = clusters[cluster_name]["kube_pwd"]
        log.logger.info(f"Configuration loaded for cluster: {cluster_name}")
        
        # Initialize deployment utilities
        deploy = Utils(config_dict)
        log.logger.info("Utils object created successfully")
        
        # OpenShift login
        success = deploy.ocp_login()
        log.logger.info(f"ocp_login returned: {success}")
        if not success:
            raise Exception("OpenShift login failed")
        log.logger.info('Logged in to ocp')
        
        # Update data configuration using our FIXED version
        # NOTE: We're using pathupdate_dataconfig_fixed() instead of deploy.pathupdate_dataconfig()
        # because the original function in utils_class.py has issues with error handling
        log.logger.info('Updating the path configuration in the data config using FIXED function.')
        result = pathupdate_dataconfig_fixed(deploy)
        log.logger.info(f"FIXED pathupdate_dataconfig returned: {result}")
        
        if not result:
            log.logger.error('Updating the Paths in data.config file failed')
            raise Exception("Updating the path in the data.config file is Failed.")
        
        # Clone repository
        log.logger.info(f'Clonning the {branch} repository.')
        clonning = deploy.cloning_repo()
        log.logger.info(f'Clonning status is {clonning}')
        if clonning == False:
            log.logger.error('Clonning failed.')
            raise Exception("Clonning failed. Please check the logs for more details.")
        
        # Setup OpenShift cluster
        setup_openshift_cluster(deploy, project)
        
        # Browser automation
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--window-size=1920,1080"])
            context = browser.new_context(
                viewport={"width": 1920, "height": 1080}, 
                ignore_https_errors=True
            )
            page = context.new_page()
            
            # Login to console and install operators
            login_to_console(page, cluster_name, KUBE_PASS)
            install_operators(page)
            
            # Setup properties and secrets
            log.logger.info('Running the property setup.')
            property_setup = deploy.property_setup()
            if not property_setup:
                log.logger.error('Running the property setup and update failed.')
                raise Exception("Running the property setup and update failed.")
            
            # Validating the generated property
            validation_status = deploy.validate_generate()
            if not validation_status:
                log.logger.error('Running the validation of property failed.')
                raise Exception("Running the validation of property failed.")
                
            # Creating the secrets
            log.logger.info('Creating secret.')
            secret_status = deploy.create_secret()
            if not secret_status:
                log.logger.error('Create secret failed.')
                raise Exception("Create secret failed.")
            
            # Configure database
            configure_database(deploy, db, external_db, tablespace_option)
            
            # Validation of the resources
            log.logger.info('Running the validation of resources.')
            validation_status = deploy.validate_resources()
            if not validation_status:
                log.logger.error('Running the validation on resources such as secret ldap, db is failed.')
                raise Exception("Running the validation on resources such as secret ldap, db is failed.")
            
            # Create content configuration
            wait_and_reload(page)
            click_Create_Content(page)
            log.logger.info('clicked create content button')
            
            log.logger.info('filling optional components')
            create_content_Optional_Components(page)

            log.logger.info('filling shared configuration')
            create_content_Shared_Configuration(page)

            configure_ldap_and_db(page, ldap, db)

            log.logger.info('filling Initialization_Configuration')
            create_content_Initialization_Configuration(page)
            
            safe_click(page, Locators.create_content_button)
            log.logger.info('CR CREATED SUCCESSFULLY')
            
            context.close()
            browser.close()
    
    except SystemExit as e:
        log.logger.error(f"Script stopped due to critical failure: {e}")
        raise
    
    except Exception as e:
        log.logger.error(f"Unexpected error: {e}")
        raise
    
    finally:
        # Safe cleanup
        for obj in ['page', 'context', 'browser']:
            if obj in locals():
                try:
                    locals()[obj].close()
                except Exception:
                    pass


if __name__ == "__main__":
    main()