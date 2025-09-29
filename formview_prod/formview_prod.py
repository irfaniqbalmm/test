#!/usr/bin/env python3

import sys
import logging
import os
import json
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


def debug_pathupdate_dataconfig(deploy, config_dict):
    """
    Debug helper to diagnose pathupdate_dataconfig issues
    """
    log.logger.info("=" * 80)
    log.logger.info("DEBUGGING pathupdate_dataconfig")
    log.logger.info("=" * 80)
    
    # 1. Check branch value
    log.logger.info(f"deploy.branch value: '{deploy.branch}'")
    log.logger.info(f"deploy.branch type: {type(deploy.branch)}")
    log.logger.info(f"Branch from config: '{config_dict.get('branch')}'")
    
    # 2. Check if branch condition will pass
    will_execute = deploy.branch != '24.0.0'
    log.logger.info(f"Will pathupdate execute? {will_execute}")
    if not will_execute:
        log.logger.warning("⚠️  Function will SKIP due to branch == '24.0.0'")
    
    # 3. Check project name and separation duty
    log.logger.info(f"deploy.project_name: '{deploy.project_name}'")
    log.logger.info(f"deploy.separation_duty_on: '{deploy.separation_duty_on}'")
    if hasattr(deploy, 'operand_namespace_suffix'):
        log.logger.info(f"deploy.operand_namespace_suffix: '{deploy.operand_namespace_suffix}'")
    
    # 4. Check data.config file
    current_dir = os.getcwd()
    dataconfig_path = os.path.join(current_dir, 'config', 'data.config')
    
    log.logger.info(f"Current directory: {current_dir}")
    log.logger.info(f"Expected data.config path: {dataconfig_path}")
    log.logger.info(f"data.config exists? {os.path.exists(dataconfig_path)}")
    
    if os.path.exists(dataconfig_path):
        log.logger.info(f"data.config size: {os.path.getsize(dataconfig_path)} bytes")
        log.logger.info(f"data.config readable? {os.access(dataconfig_path, os.R_OK)}")
        log.logger.info(f"data.config writable? {os.access(dataconfig_path, os.W_OK)}")
        
        # Backup and show first 30 lines
        try:
            backup_path = dataconfig_path + ".backup"
            shutil.copy2(dataconfig_path, backup_path)
            log.logger.info(f"Created backup at: {backup_path}")
            
            with open(dataconfig_path, 'r') as f:
                lines = f.readlines()[:30]
            log.logger.info(f"First 30 lines of data.config:")
            for i, line in enumerate(lines, 1):
                log.logger.info(f"  Line {i}: {line.rstrip()}")
                
        except Exception as e:
            log.logger.error(f"Error reading data.config: {e}")
    else:
        log.logger.error("⚠️  data.config NOT FOUND!")
    
    # 5. Check database type
    if hasattr(deploy, 'db'):
        log.logger.info(f"deploy.db: '{deploy.db}'")
        
        if deploy.db == 'postgres':
            scriptpath = os.path.join(current_dir, 'certs/scripts/ibm-cp4ba-db-ssl-cert-secret-for-postgres.sh')
            log.logger.info(f"Postgres script path: {scriptpath}")
            log.logger.info(f"Postgres script exists? {os.path.exists(scriptpath)}")
    
    # 6. Test sed command manually
    log.logger.info("\n" + "=" * 80)
    log.logger.info("Testing pattern matching:")
    test_replace_from = 'cp4ba-prerequisites/propertyfile'
    test_replace_with = f'cp4ba-prerequisites/project/{deploy.project_name}/propertyfile'
    
    log.logger.info(f"  Replace FROM: {test_replace_from}")
    log.logger.info(f"  Replace TO: {test_replace_with}")
    
    if os.path.exists(dataconfig_path):
        # Check if the pattern exists in file
        try:
            with open(dataconfig_path, 'r') as f:
                content = f.read()
            
            count = content.count(test_replace_from)
            log.logger.info(f"  Pattern '{test_replace_from}' appears {count} times in data.config")
            
            if count == 0:
                log.logger.warning(f"⚠️  Pattern NOT FOUND in data.config!")
                log.logger.info("  Searching for similar patterns:")
                for line in content.split('\n'):
                    if 'propertyfile' in line or 'cp4ba-prerequisites' in line:
                        log.logger.info(f"    Found: {line.strip()}")
                        
        except Exception as e:
            log.logger.error(f"Error checking pattern: {e}")
    
    log.logger.info("=" * 80)
    log.logger.info("END DEBUGGING")
    log.logger.info("=" * 80 + "\n")


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
        
        # ========== DEBUG SECTION START ==========
        debug_pathupdate_dataconfig(deploy, config_dict)
        # ========== DEBUG SECTION END ==========
        
        # Update data configuration
        log.logger.info('Updating the path configuration in the data config.')
        result = deploy.pathupdate_dataconfig()
        log.logger.info(f"pathupdate_dataconfig returned: {result}")
        
        # ========== VERIFICATION SECTION START ==========
        if not result:
            log.logger.error('⚠️  pathupdate_dataconfig returned False!')
            log.logger.error('Check the logs above for the actual error')
        else:
            log.logger.info('✓ pathupdate_dataconfig completed successfully')
            
            # Verify the changes were made
            dataconfig_path = os.path.join(os.getcwd(), 'config', 'data.config')
            if os.path.exists(dataconfig_path):
                with open(dataconfig_path, 'r') as f:
                    content = f.read()
                expected_pattern = f'cp4ba-prerequisites/project/{deploy.project_name}/propertyfile'
                if expected_pattern in content:
                    log.logger.info(f'✓ Verified: Found pattern "{expected_pattern}" in data.config')
                else:
                    log.logger.warning(f'⚠️  Pattern "{expected_pattern}" NOT found in data.config after update')
        # ========== VERIFICATION SECTION END ==========
        
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