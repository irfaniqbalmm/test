from cp4ba_proddeploy_automation.utils.utils_class import *
from cp4ba_proddeploy_automation.utils.logs import *
from formview_prod.formview_util import *
from formview_prod.formview_locators import *
from formview_prod.formview_data import *
from playwright.sync_api import sync_playwright
import time

log = DeploymentLogs(logname="formview_prod")
logger = log.logger

config_dict = json.loads(sys.argv[1])
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
egress = config_dict.get('egress', 'No')
component_names = config_dict.get('component_names', '')
fisma = config_dict.get('fisma', 'NO')
        
#Creating the object with the passed values
deploy = Utils(config_dict)

def install_ibm_cert_manager_Operator(page):
    """Install IBM Cert Manager Operator with improved retry logic"""
    try:
        log.logger.info("Installing IBM Cert Manager Operator")
        
        # Initial navigation and setup
        safe_click(page, Locators.operators)
        safe_click(page, Locators.operatorhub)
        safe_click(page, Locators.filter_by_keyword)
        safe_fill(page, Locators.filter_by_keyword, "cert manager")
        safe_click(page, Locators.ibm_cert_manager)
        safe_click(page, Locators.install_side)
        wait_for_seconds(20)  

        # # Use the retry function to find update channel
        # if force_element_visibility(page, Locators.update_channel):
        #     safe_scroll(page, Locators.update_channel)
        #     safe_click(page, Locators.channel_dd)
        #     safe_click(page, Locators.option_1)
        # else:
        #     # Mandatory scroll must happen even if element not found
        #     log.logger.error("All attempts failed, forcing scroll anyway")
        #     safe_scroll(page, Locators.update_channel)
        #     raise SystemExit("Cannot find Update channel after all attempts")
        
        # Continue with rest of installation
        # safe_click(page, Locators.version_dd)
        # safe_click(page, Locators.option_1)
        radio_button_click(page, Locators.operator_recommended_namespace_rb)
        radio_button_click(page, Locators.automatic_rb)
        safe_scroll(page, Locators.install_operator)
        safe_click(page, Locators.install_operator)
        click_if_found(page, Locators.install_error)
        
        log.logger.info("IBM Cert Manager Operator installation triggered.")
        
    except Exception as e:
        log.logger.error(f"Error during Cert Manager Operator installation: {e}")
        raise SystemExit(f"Stopping script due to Cert Manager Operator installation failure: {e}")


def install_ibm_licensing_Operator(page):
    """Performs the full installation flow for IBM Licensing Operator via operatorhub."""
    try:
        log.logger.info("Installing IBM Licensing Operator")
        safe_click(page, Locators.operators)
        safe_click(page, Locators.operatorhub)
        safe_click(page, Locators.filter_by_keyword)
        safe_fill(page, Locators.filter_by_keyword, "licensing")
        safe_click(page, Locators.ibm_licensing)
        safe_click(page, Locators.install_side)
        wait_for_seconds(20)
        page.screenshot(path="/opt/Cp4ba-Automation/formview_prod/screenshot2.png")
            
        # Use the retry function to find update channel
        # if force_element_visibility(page, Locators.update_channel):
        #     safe_scroll(page, Locators.update_channel)
        #     safe_click(page, Locators.channel_dd)
        #     safe_click(page, Locators.option_1)
        # else:
        #     # Mandatory scroll must happen even if element not found
        #     log.logger.error("All attempts failed, forcing scroll anyway")
        #     safe_scroll(page, Locators.update_channel)
        #     raise SystemExit("Cannot find Update channel after all attempts")
        
        # Continue with rest of installation
        # safe_click(page, Locators.version_dd)
        # safe_click(page, Locators.option_1)
        radio_button_click(page, Locators.specific_namespace_rb)
        radio_button_click(page, Locators.operator_recommended_namespace_rb)
        radio_button_click(page, Locators.automatic_rb)
        safe_scroll(page, Locators.install_operator)
        safe_click(page, Locators.install_operator)
        click_if_found(page, Locators.install_error)
        log.logger.info("IBM Licensing Operator installation triggered.")
    except Exception as e:
        log.logger.error(f"Error during IBM Licensing Operator installation: {e}")
        raise SystemExit(f"Stopping script due to IBM Licensing Operator installation failure: {e}")

def install_ibm_cp4ba_filenet_content_manager(page):
    """Performs the full installation flow for IBM CP4BA FileNet Content Manager via operatorhub."""
    try:
        log.logger.info("Installing IBM CP4BA FileNet Content Manager")
        safe_click(page, Locators.operators)
        safe_click(page, Locators.operatorhub)
        safe_click(page, Locators.filter_by_keyword)
        safe_fill(page, Locators.filter_by_keyword, "CP4BA")
        safe_click(page, Locators.ibm_cp4ba_filenet_content_manager)
        safe_click(page, Locators.install_side)
        wait_for_seconds(20)
       
        # # Use the retry function to find update channel
        # if force_element_visibility(page, Locators.update_channel):
        #     safe_scroll(page, Locators.update_channel)
        #     safe_click(page, Locators.channel_dd)
        #     safe_click(page, Locators.option_1)
        # else:
        #     # Mandatory scroll must happen even if element not found
        #     log.logger.error("All attempts failed, forcing scroll anyway")
        #     safe_scroll(page, Locators.update_channel)
        #     raise SystemExit("Cannot find Update channel after all attempts")
        
        # # Continue with rest of installation
        # safe_click(page, Locators.version_dd)
        # safe_click(page, Locators.option_1)
        radio_button_click(page, Locators.specific_namespace_rb)
        safe_click(page, Locators.installed_namespace)
        click_and_fill(page, Locators.select_project, project)
        safe_click(page, f"//button[contains(text(), 'Create Project')]/following::span[contains(@class, 'co-resource-item__resource-name') and text()='{project}']")
        radio_button_click(page, Locators.automatic_rb)
        safe_scroll(page, Locators.install_operator)
        safe_click(page, Locators.install_operator)
        click_if_found(page, Locators.install_error)
        log.logger.info("IBM CP4BA FileNet Content Manager installation triggered.")
    except Exception as e:
        log.logger.error(f"Error during IBM CP4BA FileNet Content Manager installation: {e}")
        raise SystemExit(f"Stopping script due to IBM CP4BA FileNet Content Manager installation failure: {e}")
    
def wait_for_installation(page, max_wait=1200, interval=30):
    """
    Waits until all expected CP4BA operator components show 'Succeeded' status.
    """
    safe_click(page, Locators.operators)
    safe_click(page, Locators.installed_operators)

    selectors = [
        Locators.ibm_cert_manager_success_check,
        Locators.ibm_cloud_pak_foundational_services_success_check,
        Locators.ibm_cp4ba_filenet_content_manager_success_check,
        Locators.ibm_cloud_pak_for_business_automation_cp4ba_multipattern_success_check,
        Locators.ibm_cp4ba_workflow_process_service_success_check,
        Locators.ibm_cp4ba_insights_engine_success_check,
        Locators.ibm_cp4ba_process_federation_server_success_check,
        Locators.ibm_business_automation_workflow_runtime_and_workstream_services_success_check,
        Locators.operand_deployment_lifecycle_manager_success_check
    ]

    deadline = time.time() + max_wait
    pending = set(selectors)  # track only missing ones

    while time.time() < deadline:
        for selector in list(pending):
            try:
                # Wait only for this interval
                page.wait_for_selector(selector, timeout=interval*1000, state="visible")
                log.logger.info(f"Success: {selector} reached 'Succeeded' status.")
                pending.remove(selector)
            except Exception:
                log.logger.info(f"Waiting: {selector}")
        if not pending:
            log.logger.info("All CP4BA operators have reached 'Succeeded' status.")
            return True
        time.sleep(interval)

    raise TimeoutError(
        f"Timeout after {max_wait//60} minutes. Still missing: {', '.join(pending)}"
    )

def click_Create_Content(page):
    """Performs Stariting the CR creation process."""
    try:
        log.logger.info("Clicking Create Content Button.")
        safe_click(page, Locators.operators)
        safe_click(page, Locators.installed_operators)
        safe_click(page, Locators.namespace_dd)
        safe_click(page, f"//span[text()='{project}']")
        safe_click(page, Locators.cp4ba_filenet_content_manager_deployment)
        safe_click(page, Locators.create_content)
        safe_click(page, Locators.formview)
        log.logger.info("Create Content Clicked.")
    except Exception as e:
        log.logger.error(f"Error during Create Content Click: {e}")
        raise SystemExit(f"Stopping script due Error during Create Content Click: {e}")

def create_content_Optional_Components(page):
    """Performs selecting Optional_Components in CR."""
    try:
        log.logger.info("Filling Optional Components in CR.")
        safe_click(page, Locators.license)
        safe_click(page, Locators.license_accept)
        safe_click(page, Locators.optional_component)
        safe_click(page, Locators.bai)
        safe_click(page, Locators.css)
        safe_click(page, Locators.cmis)
        safe_click(page, Locators.tm)
        safe_click(page, Locators.ier)
        safe_click(page, Locators.iccsap)
        safe_click(page, Locators.deployment_type)
        safe_click(page, Locators.production_oc)

        log.logger.info("Configured Optional Components.")
    except Exception as e:
        log.logger.error(f"Error during Optional Components Configuration: {e}")
        raise SystemExit(f"Stopping script due to Error during Optional Components Configuration: {e}")

def create_content_Shared_Configuration(page):
    """Performs the Configuration for Shared Configuration in CR"""
    try:
        log.logger.info("Filling Shared Configuration in CR.")
        safe_click(page, Locators.shared_configuration)
        safe_click(page, Locators.select_purchased_fncm_license)
        safe_click(page, Locators.production_sc)
        safe_click(page, Locators.platform_dd)
        safe_click(page, Locators.ocp)
        safe_fill_with_clear(page, Locators.root_ca_secret, 'icp4a-root-ca')
        safe_fill(page, Locators.sc_drivers_url, 'http://cp4ba-jenkins1.fyre.ibm.com:8887/jdbc.zip')
        safe_click(page, Locators.profile_size)
        safe_click(page, Locators.profile_size_small)
        

        if branch >= "25.0.0":
            if egress == "Yes":
                set_checkbox_state(
                    page,
                    input_selector=Locators.sample_network_policies_input,
                    toggle_selector=Locators.sample_network_policies_toggle,
                    should_be_checked=True 
                )
            else:
                set_checkbox_state(
                    page,
                    input_selector=Locators.sample_network_policies_input,
                    toggle_selector=Locators.sample_network_policies_toggle,
                    should_be_checked=False
                )
        else:
            safe_click(page, Locators.cp4ba_egress_settings)
            if egress == "Yes":
                set_checkbox_state(
                    page,
                    input_selector=Locators.egress_input,
                    toggle_selector=Locators.egress_toggle,
                    should_be_checked=True 
                )
            else:
                set_checkbox_state(
                    page,
                    input_selector=Locators.egress_input,
                    toggle_selector=Locators.egress_toggle,
                    should_be_checked=False
                )
        
        
        safe_click(page, Locators.storage_configuration)
        safe_click(page, Locators.block_storage_class_button)
        safe_fill(page, Locators.select_storage_class, 'managed-nfs-storage')
        safe_click(page, Locators.block_storage_class_managed_nfs_storage)
        safe_click(page, Locators.slow_storage_class_button)
        safe_fill(page, Locators.select_storage_class, 'managed-nfs-storage')
        safe_click(page, Locators.slow_storage_class_managed_nfs_storage)
        safe_click(page, Locators.medium_storage_class_button)
        safe_fill(page, Locators.select_storage_class, 'managed-nfs-storage')
        safe_click(page, Locators.medium_storage_class_managed_nfs_storage)
        safe_click(page, Locators.fast_storage_class_button)
        safe_fill(page, Locators.select_storage_class, 'managed-nfs-storage')
        safe_click(page, Locators.fast_storage_class_managed_nfs_storage)

        set_checkbox_state(
                    page,
                    input_selector=Locators.content_initialization_input,
                    toggle_selector=Locators.content_initialization_toggle,
                    should_be_checked=True 
                )
        set_checkbox_state(
                    page,
                    input_selector=Locators.content_verification_input,
                    toggle_selector=Locators.content_verification_toggle,
                    should_be_checked=True 
                )
        
        if fips == "Yes":
            set_checkbox_state(
                page,
                input_selector=Locators.fips_input,
                toggle_selector=Locators.fips_toggle,
                should_be_checked=True 
            )
        else:
            set_checkbox_state(
                page,
                input_selector=Locators.fips_input,
                toggle_selector=Locators.fips_toggle,
                should_be_checked=False
            )
        

        log.logger.info("Configured Shared Configuration.")
    except Exception as e:
        log.logger.error(f"Error during Shared Configuration: {e}")
        raise SystemExit(f"Stopping script due to Error during Shared Configuration: {e}")
 
def create_content_Initialization_Configuration(page):
    """Performs selecting Initialization_Configuration in CR."""
    try:
        log.logger.info("Filling Initialization_Configuration in CR.")
        safe_click(page, Locators.initialization_configuration)
        safe_click(page, Locators.ldap_creation)
        safe_click(page, Locators.ldap_administrator_user)
        safe_click(page, Locators.add_ldap_administrator_user)
        safe_click(page, Locators.ldap_admin_group_name)
        
        if db == "tds":
            safe_fill(page, Locators.ldap_administrator_user_input, 'group0001usr0001')
            safe_fill(page, Locators.ldap_admin_group_name_input, 'group0001')
        if db == "msad":
            safe_fill(page, Locators.ldap_administrator_user_input, 'Testa1SpecialChar$')
            safe_fill(page, Locators.ldap_admin_group_name_input, 'Administrators')

        safe_click(page, Locators.object_store_creation)
        safe_click(page, Locators.object_store_details)
        safe_fill_with_clear(page, Locators.object_store_display_name, 'OS01')
        safe_fill_with_clear(page, Locators.object_store_symbolic_name, 'OS01')
        safe_click(page, Locators.object_store_connection_details)
        safe_fill_with_clear(page, Locators.object_store_connection_name, 'objectstore1_connection')
        safe_fill_with_clear(page, Locators.object_store_datasource_name, 'FNOS1DS')
        safe_fill_with_clear(page, Locators.object_store_xa_datasource_name, 'FNOS1DSXA')
        safe_click(page, Locators.object_store_admin_user_groups)
        safe_click(page, Locators.add_object_store_admin_user_groups)
        if db == "msad":
            safe_fill(page, Locators.object_store_admin_user_groups_input, 'Administrators')
        if db == "tds":
            safe_fill(page, Locators.object_store_admin_user_groups_input, 'group0001')

        safe_click(page, Locators.object_store_enable_workflow_toggle)

        if db == "msad":
            safe_fill(page, Locators.object_store_table_space, 'PRIMARY')
        if db == "tds":
            safe_fill(page, Locators.object_store_table_space, 'OS1_BANDATATS')
        
        if db == "msad":
            safe_fill(page, Locators.object_store_workflow_admin_group, 'Administrators')
            safe_fill(page, Locators.object_store_workflow_config_group, 'Administrators')
        if db == "tds":
            safe_fill(page, Locators.object_store_workflow_admin_group, 'group0001')
            safe_fill(page, Locators.object_store_workflow_config_group, 'group0001')
        

        safe_fill(page, Locators.object_store_connection_point_for_workflow, 'pe_conn_os1')

        safe_click(page, Locators.navigator_initialization_configuration)
        safe_click(page, Locators.navigator_repository)
        safe_click(page, Locators.add_navigator_repository)
        safe_fill(page, Locators.fncm_repository_identification_id, 'demo_repo1')
        safe_fill(page, Locators.fncm_repository_wsi_url, "https://{{ meta.name }}-cpe-stateless-svc.{{ meta.namespace }}.svc:9443/wsi/FNCEWS40MTOM/")
        safe_fill(page, Locators.fncm_object_store_symbolic_name, 'OS01')
        safe_fill(page, Locators.fncm_object_store_display_name, 'OS01')
        safe_click(page, Locators.enable_workflow_for_fncm_repository_toggle)
        safe_fill(page, Locators.fncm_repository_connection_point, 'pe_conn_os1:1')
        safe_fill(page, Locators.fncm_repository_protocol, 'FileNetP8WSI')

        safe_click(page, Locators.navigator_desktop_configuration)
        safe_click(page, Locators.add_navigator_desktop_configuration)
        safe_fill(page, Locators.navigator_desktop_id, 'demo')
        safe_fill(page, Locators.navigator_desktop_name, 'icn_desktop')
        safe_fill(page, Locators.navigator_desktop_description, 'This is ICN desktop')
        safe_click(page, Locators.enable_navigator_desktop_as_default_toggle)
        safe_fill(page, Locators.navigator_repository_id, 'demo_repo1')
        safe_click(page, Locators.enable_workflow_for_navigator_desktop_toggle)

        log.logger.info("Configured Initialization Configuration.")
    except Exception as e:
        log.logger.error(f"Error during Initialization Configuration: {e}")
        raise SystemExit(f"Stopping script due to Error during Initialization Configuration: {e}")




def create_content_LDAP_Configuration_MSAD(page):
    """Performs the Configuration for LDAP Configuration MSAD in CR"""
    try:
        log.logger.info("Filling LDAP Configuration MSAD in CR.")
        safe_click(page, Locators.ldap_configuration)
        safe_fill(page, Locators.directory_service_server_host_name, 'testa1.fyre.ibm.com')
        safe_fill_with_clear(page, Locators.directory_service_server_port_number, '636')
        safe_click(page, Locators.directory_service_server_bind_secret)
        safe_fill(page, Locators.select_secret, 'ldap-bind-secret')
        safe_click(page, Locators.ldap_bind_secret)
        safe_fill(page, Locators.base_entry_distinguished_name_repository, 'DC=testa1,DC=fyre,DC=ibm,DC=COM')
        safe_fill_with_clear(page, Locators.directory_service_server_username_attribute, 'user:sAMAccountName')
        safe_fill_with_clear(page, Locators.directory_service_server_user_display_name_attribute, 'sAMAccountName')
        safe_fill(page, Locators.base_group_entry_distinguished_name_repository, 'DC=testa1,DC=fyre,DC=ibm,DC=COM')
        safe_fill_with_clear(page, Locators.directory_service_server_group_name_attribute, '*:cn')
        safe_fill_with_clear(page, Locators.directory_service_server_group_display_name_attribute, 'cn')
        safe_fill_with_clear(page, Locators.directory_service_server_group_membership_search_filter, '(&(cn=%v)(objectcategory=group))')
        safe_fill_with_clear(page, Locators.directory_service_server_group_member_id_map, 'memberOf:member')
        safe_click(page, Locators.directory_service_provider)
        safe_click(page, Locators.microsoft_active_directory)
        safe_click(page, Locators.ad)
        safe_fill_with_clear(page, Locators.ad_lc_user_filter, '(&(sAMAccountName=%v)(objectcategory=user))')
        safe_fill_with_clear(page, Locators.ad_lc_group_filter, '(&(cn=%v)(objectcategory=group))')
        ldap_ssl = "Yes"
        if ldap_ssl == "Yes":
            set_checkbox_state(
                page,
                input_selector=Locators.ldap_ssl_input,
                toggle_selector=Locators.ldap_ssl_toggle,
                should_be_checked=True 
            )
        else:
            set_checkbox_state(
                page,
                input_selector=Locators.ldap_ssl_input,
                toggle_selector=Locators.ldap_ssl_toggle,
                should_be_checked=False
            )
        
        safe_click(page, Locators.directory_service_server_ssl_tls_certificate_secret)
        safe_fill(page, Locators.select_secret, 'ibm-cp4ba-ldap-ssl-secret')
        safe_click(page, Locators.ibm_cp4ba_ldap_ssl_secret)
        log.logger.info("Configured LDAP Configuration MSAD.")
    except Exception as e:
        log.logger.error(f"Error during LDAP Configuration MSAD: {e}")
        raise SystemExit(f"Stopping script due to Error during LDAP Configuration MSAD: {e}")


def create_content_LDAP_Configuration_TDS(page):
    """Performs the Configuration for LDAP Configuration TDS in CR"""
    try:
        log.logger.info("Filling LDAP Configuration with TDS")
        safe_click(page, Locators.ldap_configuration)
        safe_fill(page, Locators.directory_service_server_host_name, 'seepage1.fyre.ibm.com')
        safe_fill_with_clear(page, Locators.directory_service_server_port_number, '636')
        safe_click(page, Locators.directory_service_server_bind_secret)
        safe_fill(page, Locators.select_secret, 'ldap-bind-secret')
        safe_click(page, Locators.ldap_bind_secret)
        safe_fill(page, Locators.base_entry_distinguished_name_repository, 'DC=EXAMPLE,DC=COM')
        safe_fill_with_clear(page, Locators.directory_service_server_username_attribute, '*:uid')
        safe_fill_with_clear(page, Locators.directory_service_server_user_display_name_attribute, 'cn')
        safe_fill(page, Locators.base_group_entry_distinguished_name_repository, 'DC=EXAMPLE,DC=COM')
        safe_fill_with_clear(page, Locators.directory_service_server_group_name_attribute, '*:cn')
        safe_fill_with_clear(page, Locators.directory_service_server_group_display_name_attribute, 'cn')
        safe_fill_with_clear(page, Locators.directory_service_server_group_membership_search_filter, '(|(&(objectclass=groupofnames)(member={0}))(&(objectclass=groupofuniquenames)(uniquemember={0})))')
        safe_fill_with_clear(page, Locators.directory_service_server_group_member_id_map, 'groupofnames:member')
        safe_click(page, Locators.directory_service_provider)
        safe_click(page, Locators.ibm_security_directory_server)
        safe_click(page, Locators.tds)
        safe_fill_with_clear(page, Locators.tds_lc_user_filter, '(&(cn=%v)(objectclass=person))')
        safe_fill_with_clear(page, Locators.tds_lc_group_filter, '(&(cn=%v)(|(objectclass=groupofnames)(objectclass=groupofuniquenames)(objectclass=groupofurls)))')
        
        ldap_ssl = "Yes"
        if ldap_ssl == "Yes":
            set_checkbox_state(
                page,
                input_selector=Locators.ldap_ssl_input,
                toggle_selector=Locators.ldap_ssl_toggle,
                should_be_checked=True 
            )
        else:
            set_checkbox_state(
                page,
                input_selector=Locators.ldap_ssl_input,
                toggle_selector=Locators.ldap_ssl_toggle,
                should_be_checked=False
            ) 

        safe_click(page, Locators.directory_service_server_ssl_tls_certificate_secret)
        safe_fill(page, Locators.select_secret, 'ibm-cp4ba-ldap-ssl-secret')
        safe_click(page, Locators.ibm_cp4ba_ldap_ssl_secret)

        

        log.logger.info("Configured LDAP Configuration TDS.")
    except Exception as e:
        log.logger.error(f"Error during LDAP Configuration TDS: {e}")
        raise SystemExit(f"Stopping script due to Error during LDAP Configuration TDS: {e}")

def create_content_DB_Configuration_MSSQL(page):
    """Performs the Configuration for DB Configuration MSSQL in CR"""
    try:
        log.logger.info("Filling DB Configuration MSSQL in CR.")
        safe_click(page, Locators.database_configuration)
        
        db_ssl = "Yes"
        if db_ssl == "Yes":
            set_checkbox_state(
                page,
                input_selector=Locators.db_ssl_input,
                toggle_selector=Locators.db_ssl_toggle,
                should_be_checked=True 
            )
        else:
            set_checkbox_state(
                page,
                input_selector=Locators.db_ssl_input,
                toggle_selector=Locators.db_ssl_toggle,
                should_be_checked=False
            ) 
        db_precheck = "No"
        if db_precheck == "Yes":
            set_checkbox_state(
                page,
                input_selector=Locators.db_precheck_input,
                toggle_selector=Locators.db_precheck_toggle,
                should_be_checked=True 
            )
        else:
            set_checkbox_state(
                page,
                input_selector=Locators.db_precheck_input,
                toggle_selector=Locators.db_precheck_toggle,
                should_be_checked=False
            ) 
        safe_click(page, Locators.gcd_datasource_configuration)
        safe_fill_with_clear(page, Locators.gcd_non_xa_datasource_name, 'FNGCDDS')
        safe_fill_with_clear(page, Locators.gcd_xa_datasource_name, 'FNGCDDSXA')
        safe_fill_with_clear(page, Locators.gcd_database_name, 'GCDDB_BSH') #db name how to get
        safe_fill_with_clear(page, Locators.gcd_database_server_name, 'mssqlrtp1.fyre.ibm.com')
        safe_fill_with_clear(page, Locators.gcd_database_server_port, '1433')
        safe_click(page, Locators.gcd_db_ssl_certificate_secret)
        safe_fill(page, Locators.select_secret, 'ibm-cp4ba-db-ssl-secret-for-db')
        safe_click(page, Locators.gcd_ibm_cp4ba_db_ssl_secret_for_db)
        safe_click(page, Locators.gcd_database_type)
        safe_click(page, Locators.gcd_database_type_sqlserver)
        
        safe_click(page, Locators.content_management_os_datasource_configuration)
        safe_click(page, Locators.os1_database_type)
        safe_click(page, Locators.gcd_database_type_sqlserver)
        safe_fill_with_clear(page, Locators.object_store_label_for_content_management, 'os1')
        safe_fill_with_clear(page, Locators.os1_non_xa_datasource_name, 'FNOS1DS')
        safe_fill_with_clear(page, Locators.os1_xa_datasource_name, 'FNOS1DSXA') 
        safe_fill_with_clear(page, Locators.os1_database_server_name, 'mssqlrtp1.fyre.ibm.com')
        safe_fill_with_clear(page, Locators.os1_database_name, 'OS1DB_BSH')  #db name how to get
        safe_fill_with_clear(page, Locators.os1_database_server_port, '1433')
        safe_click(page, Locators.os1_db_ssl_certificate_secret)
        safe_fill(page, Locators.select_secret, 'ibm-cp4ba-db-ssl-secret-for-db')
        safe_click(page, Locators.os1_ibm_cp4ba_db_ssl_secret_for_db)
        
        safe_click(page, Locators.navigator_datasource_configuration)
        safe_fill_with_clear(page, Locators.navigator_datasource_name, 'ECMClientDS') 
        safe_fill_with_clear(page, Locators.navigator_database_server_name, 'mssqlrtp1.fyre.ibm.com')
        safe_fill_with_clear(page, Locators.navigator_database_name, 'ICNDB_BSH')  #db name how to get
        safe_fill_with_clear(page, Locators.navigator_database_server_port, '1433')
        safe_click(page, Locators.navigator_db_ssl_certificate_secret)
        safe_fill(page, Locators.select_secret, 'ibm-cp4ba-db-ssl-secret-for-db')
        safe_click(page, Locators.navigator_ibm_cp4ba_db_ssl_secret_for_db)
        safe_click(page, Locators.navigator_database_type)
        safe_click(page, Locators.gcd_database_type_sqlserver)
        log.logger.info("Configured DB Configuration MSSQL.")
    except Exception as e:
        log.logger.error(f"Error during DB Configuration MSSQL: {e}")
        raise SystemExit(f"Stopping script due to Error during DB Configuration MSSQL: {e}")

def create_content_DB_Configuration_ORACLE(page):
    """Performs the Configuration for DB Configuration ORACLE in CR"""
    try:
        log.logger.info("Filling DB Configuration ORACLE in CR.")
        safe_click(page, Locators.database_configuration)

        db_ssl = "Yes"
        if db_ssl == "Yes":
            set_checkbox_state(
                page,
                input_selector=Locators.db_ssl_input,
                toggle_selector=Locators.db_ssl_toggle,
                should_be_checked=True 
            )
        else:
            set_checkbox_state(
                page,
                input_selector=Locators.db_ssl_input,
                toggle_selector=Locators.db_ssl_toggle,
                should_be_checked=False
            ) 
        db_precheck = "No"
        if db_precheck == "Yes":
            set_checkbox_state(
                page,
                input_selector=Locators.db_precheck_input,
                toggle_selector=Locators.db_precheck_toggle,
                should_be_checked=True 
            )
        else:
            set_checkbox_state(
                page,
                input_selector=Locators.db_precheck_input,
                toggle_selector=Locators.db_precheck_toggle,
                should_be_checked=False
            ) 

        safe_click(page, Locators.gcd_datasource_configuration)
        safe_fill_with_clear(page, Locators.gcd_non_xa_datasource_name, 'FNGCDDS')
        safe_fill_with_clear(page, Locators.gcd_xa_datasource_name, 'FNGCDDSXA')
        safe_fill_with_clear(page, Locators.gcd_database_name, 'ORCLPDB1GCD') #db name how to get
        safe_click(page, Locators.gcd_db_ssl_certificate_secret)
        safe_fill(page, Locators.select_secret, 'ibm-cp4ba-db-ssl-secret-for-db')
        safe_click(page, Locators.gcd_ibm_cp4ba_db_ssl_secret_for_db)
        safe_click(page, Locators.gcd_database_type)
        safe_click(page, Locators.gcd_database_type_oracle)
        safe_fill(page, Locators.gcd_oracle_db_connection_string, 'jdbc:oracle:thin:@(DESCRIPTION=(ADDRESS=(PROTOCOL=TCPS)(HOST=oracle19svl1.fyre.ibm.com)(PORT=2484))(CONNECT_DATA=(SERVICE_NAME=ORCLPDB1)))')

        safe_click(page, Locators.content_management_os_datasource_configuration)
        safe_click(page, Locators.os1_database_type)
        safe_click(page, Locators.gcd_database_type_oracle)
        safe_fill_with_clear(page, Locators.object_store_label_for_content_management, 'os1')
        safe_fill_with_clear(page, Locators.os1_non_xa_datasource_name, 'FNOS1DS')
        safe_fill_with_clear(page, Locators.os1_xa_datasource_name, 'FNOS1DSXA') 
        safe_fill_with_clear(page, Locators.os1_database_name, 'ORCLPDB1OS1')  #db name how to get
        safe_click(page, Locators.os1_db_ssl_certificate_secret)
        safe_fill(page, Locators.select_secret, 'ibm-cp4ba-db-ssl-secret-for-db')
        safe_click(page, Locators.os1_ibm_cp4ba_db_ssl_secret_for_db)
        safe_click(page, Locators.advanced_configuration)
        safe_fill(page, Locators.os1_oracle_db_connection_string, 'jdbc:oracle:thin:@(DESCRIPTION=(ADDRESS=(PROTOCOL=TCPS)(HOST=oracle19svl1.fyre.ibm.com)(PORT=2484))(CONNECT_DATA=(SERVICE_NAME=ORCLPDB1)))')

        
        safe_click(page, Locators.navigator_datasource_configuration)
        safe_fill_with_clear(page, Locators.navigator_datasource_name, 'ECMClientDS') 
        safe_fill_with_clear(page, Locators.navigator_database_name, 'ORCLPDB1ICN')  #db name how to get
        safe_click(page, Locators.navigator_db_ssl_certificate_secret)
        safe_fill(page, Locators.select_secret, 'ibm-cp4ba-db-ssl-secret-for-db')
        safe_click(page, Locators.navigator_ibm_cp4ba_db_ssl_secret_for_db)
        safe_click(page, Locators.navigator_database_type)
        safe_click(page, Locators.gcd_database_type_oracle)
        safe_fill(page, Locators.navigator_oracle_db_connection_string, 'jdbc:oracle:thin:@(DESCRIPTION=(ADDRESS=(PROTOCOL=TCPS)(HOST=oracle19svl1.fyre.ibm.com)(PORT=2484))(CONNECT_DATA=(SERVICE_NAME=ORCLPDB1)))')

        log.logger.info("Configured DB Configuration Oracle.")
    except Exception as e:
        log.logger.error(f"Error during DB Configuration Oracle: {e}")
        raise SystemExit(f"Stopping script due to Error during DB Configuration Oracle: {e}")

def create_content_DB_Configuration_PostgressSQL(page):
    """Performs the Configuration for DB Configuration PostgressSQL in CR"""
    try:
        log.logger.info("Filling DB Configuration PostgressSQL in CR.")
        safe_click(page, Locators.database_configuration)

        db_ssl = "Yes"
        if db_ssl == "Yes":
            set_checkbox_state(
                page,
                input_selector=Locators.db_ssl_input,
                toggle_selector=Locators.db_ssl_toggle,
                should_be_checked=True 
            )
        else:
            set_checkbox_state(
                page,
                input_selector=Locators.db_ssl_input,
                toggle_selector=Locators.db_ssl_toggle,
                should_be_checked=False
            ) 
        db_precheck = "No"
        if db_precheck == "Yes":
            set_checkbox_state(
                page,
                input_selector=Locators.db_precheck_input,
                toggle_selector=Locators.db_precheck_toggle,
                should_be_checked=True 
            )
        else:
            set_checkbox_state(
                page,
                input_selector=Locators.db_precheck_input,
                toggle_selector=Locators.db_precheck_toggle,
                should_be_checked=False
            ) 

        safe_click(page, Locators.gcd_datasource_configuration)
        safe_fill_with_clear(page, Locators.gcd_non_xa_datasource_name, 'FNGCDDS')
        safe_fill_with_clear(page, Locators.gcd_xa_datasource_name, 'FNGCDDSXA')
        safe_fill_with_clear(page, Locators.gcd_database_name, 'GCDDB_BSH') #db name how to get
        safe_fill_with_clear(page, Locators.gcd_database_server_name, 'postgres171.fyre.ibm.com')
        safe_fill_with_clear(page, Locators.gcd_database_server_port, '5432')
        safe_click(page, Locators.gcd_db_ssl_certificate_secret)
        safe_fill(page, Locators.select_secret, 'ibm-cp4ba-db-ssl-secret-for-db')
        safe_click(page, Locators.gcd_ibm_cp4ba_db_ssl_secret_for_db)
        safe_click(page, Locators.gcd_database_type)
        safe_click(page, Locators.gcd_database_type_postgresql)
        
        safe_click(page, Locators.content_management_os_datasource_configuration)
        safe_click(page, Locators.os1_database_type)
        safe_click(page, Locators.gcd_database_type_postgresql)
        safe_fill_with_clear(page, Locators.object_store_label_for_content_management, 'os1')
        safe_fill_with_clear(page, Locators.os1_non_xa_datasource_name, 'FNOS1DS')
        safe_fill_with_clear(page, Locators.os1_xa_datasource_name, 'FNOS1DSXA') 
        safe_fill_with_clear(page, Locators.os1_database_server_name, 'postgres171.fyre.ibm.com')
        safe_fill_with_clear(page, Locators.os1_database_name, 'OS1DB_BSH')  #db name how to get
        safe_fill_with_clear(page, Locators.os1_database_server_port, '5432')
        safe_click(page, Locators.os1_db_ssl_certificate_secret)
        safe_fill(page, Locators.select_secret, 'ibm-cp4ba-db-ssl-secret-for-db')
        safe_click(page, Locators.os1_ibm_cp4ba_db_ssl_secret_for_db)
        
        safe_click(page, Locators.navigator_datasource_configuration)
        safe_fill_with_clear(page, Locators.navigator_datasource_name, 'ECMClientDS') 
        safe_fill_with_clear(page, Locators.navigator_database_server_name, 'postgres171.fyre.ibm.com')
        safe_fill_with_clear(page, Locators.navigator_database_name, 'ICNDB_BSH')  #db name how to get
        safe_fill_with_clear(page, Locators.navigator_database_server_port, '5432')
        safe_click(page, Locators.navigator_db_ssl_certificate_secret)
        safe_fill(page, Locators.select_secret, 'ibm-cp4ba-db-ssl-secret-for-db')
        safe_click(page, Locators.navigator_ibm_cp4ba_db_ssl_secret_for_db)
        safe_click(page, Locators.navigator_database_type)
        safe_click(page, Locators.gcd_database_type_postgresql)
        log.logger.info("Configured DB Configuration PostgreSQL.")
    except Exception as e:
        log.logger.error(f"Error during DB Configuration PostgreSQL: {e}")
        raise SystemExit(f"Stopping script due to Error during DB Configuration PostgreSQL: {e}")
    
def create_content_DB_Configuration_DB2(page):
    """Performs the Configuration for DB Configuration PostgressSQL in CR"""
    try:
        log.logger.info("Filling DB Configuration PostgressSQL in CR.")
        safe_click(page, Locators.database_configuration)

        db_ssl = "Yes"
        if db_ssl == "Yes":
            set_checkbox_state(
                page,
                input_selector=Locators.db_ssl_input,
                toggle_selector=Locators.db_ssl_toggle,
                should_be_checked=True 
            )
        else:
            set_checkbox_state(
                page,
                input_selector=Locators.db_ssl_input,
                toggle_selector=Locators.db_ssl_toggle,
                should_be_checked=False
            ) 
        db_precheck = "No"
        if db_precheck == "Yes":
            set_checkbox_state(
                page,
                input_selector=Locators.db_precheck_input,
                toggle_selector=Locators.db_precheck_toggle,
                should_be_checked=True 
            )
        else:
            set_checkbox_state(
                page,
                input_selector=Locators.db_precheck_input,
                toggle_selector=Locators.db_precheck_toggle,
                should_be_checked=False
            ) 

        safe_click(page, Locators.gcd_datasource_configuration)
        safe_fill_with_clear(page, Locators.gcd_non_xa_datasource_name, 'FNGCDDS')
        safe_fill_with_clear(page, Locators.gcd_xa_datasource_name, 'FNGCDDSXA')
        safe_fill_with_clear(page, Locators.gcd_database_name, 'GCDDB_BSH') #db name how to get
        safe_fill_with_clear(page, Locators.gcd_database_server_name, 'postgres171.fyre.ibm.com')
        safe_fill_with_clear(page, Locators.gcd_database_server_port, '5432')
        safe_click(page, Locators.gcd_db_ssl_certificate_secret)
        safe_fill(page, Locators.select_secret, 'ibm-cp4ba-db-ssl-secret-for-db')
        safe_click(page, Locators.gcd_ibm_cp4ba_db_ssl_secret_for_db)
        safe_click(page, Locators.gcd_database_type)
        safe_click(page, Locators.gcd_database_type_postgresql)
        
        safe_click(page, Locators.content_management_os_datasource_configuration)
        safe_click(page, Locators.os1_database_type)
        safe_click(page, Locators.gcd_database_type_postgresql)
        safe_fill_with_clear(page, Locators.object_store_label_for_content_management, 'os1')
        safe_fill_with_clear(page, Locators.os1_non_xa_datasource_name, 'FNOS1DS')
        safe_fill_with_clear(page, Locators.os1_xa_datasource_name, 'FNOS1DSXA') 
        safe_fill_with_clear(page, Locators.os1_database_server_name, 'postgres171.fyre.ibm.com')
        safe_fill_with_clear(page, Locators.os1_database_name, 'OS1DB_BSH')  #db name how to get
        safe_fill_with_clear(page, Locators.os1_database_server_port, '5432')
        safe_click(page, Locators.os1_db_ssl_certificate_secret)
        safe_fill(page, Locators.select_secret, 'ibm-cp4ba-db-ssl-secret-for-db')
        safe_click(page, Locators.os1_ibm_cp4ba_db_ssl_secret_for_db)
        
        safe_click(page, Locators.navigator_datasource_configuration)
        safe_fill_with_clear(page, Locators.navigator_datasource_name, 'ECMClientDS') 
        safe_fill_with_clear(page, Locators.navigator_database_server_name, 'postgres171.fyre.ibm.com')
        safe_fill_with_clear(page, Locators.navigator_database_name, 'ICNDB_BSH')  #db name how to get
        safe_fill_with_clear(page, Locators.navigator_database_server_port, '5432')
        safe_click(page, Locators.navigator_db_ssl_certificate_secret)
        safe_fill(page, Locators.select_secret, 'ibm-cp4ba-db-ssl-secret-for-db')
        safe_click(page, Locators.navigator_ibm_cp4ba_db_ssl_secret_for_db)
        safe_click(page, Locators.navigator_database_type)
        safe_click(page, Locators.gcd_database_type_postgresql)
        log.logger.info("Configured DB Configuration PostgreSQL.")
    except Exception as e:
        log.logger.error(f"Error during DB Configuration PostgreSQL: {e}")
        raise SystemExit(f"Stopping script due to Error during DB Configuration PostgreSQL: {e}")