from tomlkit import parse

from setup_env import *
from utils.logger import logger
import utils.login as login
import utils.endpoints as endpoints
import inputs.input_data as input_data
import utils.check_cr_content as check_cr_content 
import utils.create_network_policy as create_network_policy
import utils.json_to_xml as json_to_xml
from utils.clean_data import CleanFolder
from utils.clear_history_cache_cookies import ClearChrome
from utils.bvt_status import update_status
from utils.get_cr_status import DeploymentStatus
import component_pages.cpe.add_user_to_im as add_user_to_im
import component_pages.logs.get_logs as get_logs
from component_pages.ocp import OCP
from component_pages.iccsap import ICCSAP
from component_pages.bai import BaiAutomation
from component_pages.cmis import CMISAutomation
from component_pages.cmis import CMISOCPAutomation
from component_pages.graphql import GraphQLTester
from component_pages.cpe.cpe import CpeAdmin
from component_pages.cpe.filenet import Filenet
from component_pages.cpe.filenet_stateless import FilenetStateless
from component_pages.cpe.p8bpmrest import P8BPMRest
from component_pages.opensearch import Opensearch
from component_pages.navigator.nav_utility import NavigatorUtility
from component_pages.navigator.nav_cmod import NavigatorCMOD
from component_pages.navigator.nav_cm8 import NavigatorCM8
from component_pages.ier.ier import IERDownloader
from component_pages.taskmanager import TaskManagerPage
from component_pages.fisma import Fisma
from component_pages.jvm_options import JvmCustomOptions
import reports.pdf_report as pdf_report
from oc_operations.test_case import *

def handle_exception(component, exception):
    # Print the exception traceback for debugging
    logger.error(f"An exception occured during BVT of {component} : {str(exception)}.")
    logger.error("Stack Trace:", exc_info=True) 

def main():
    try: 
        login.ocp_login()
        input_data.initialize_input_data()
        endpoints.fetch_endpoints()
    except Exception as e:
        logger.info(f"An exception occured during executing the prerequisite setups: {e}")
        
    with open("./inputs/config.toml","r") as file :
        config = parse(file.read())
    deployment_type = config['configurations']['deployment_type']
    oc_verify = config['configurations']['oc_verify']

    # Get the optional components from CR
    optional_components = check_cr_content.get_optional_components()
    logger.info(f"Optional components are : {optional_components}")
    if not optional_components :
        logger.critical("Couldn't fetch optional components. Exiting BVT!!")
        exit(1)

    #Cleaning up
    clean = CleanFolder()
    clean.reset_execution_data()

    #Check if egress is True in CR
    egress_status = check_cr_content.check_egress()  
    if egress_status == "True" : 
        create_network_policy.create_network_policies()

    try :
        #Check if FIPS is True in CR
        check_cr_content.check_fips()
    except Exception as e:
        handle_exception("FIPS Check",e)

    try :
        #OCP
        ocp = OCP()
        ocp.navigate_to_installed_operators()
        ocp.navigate_to_config_maps()
        ocp.capture_init_cm()
        ocp.capture_verify_cm()
        ocp.close_browser()
    except Exception as e:
        handle_exception("OCP", e)

    try :
        #Add Non-admin User to IM
        add_user = add_user_to_im.AddUserIM()
        add_user.login_to_im()
        add_user.add_user()
    except Exception as e: 
        handle_exception("Adding user to IM",e)
    finally:
        add_user.close_browser()

    if "ICCSAP" in optional_components :
        try :
            #ICCSAP
            iccsap = ICCSAP()
            iccsap.navigate_to_iccsap()
        except Exception as e:
            handle_exception("ICCSAP", e)
        finally : 
            iccsap.close_browser()
    else : 
        update_status("ICCSAP", "N/A")

    if "CMIS" in optional_components:
        try : 
            #CMIS FIRST LINK
            cmis_automation = CMISAutomation()
            cmis_automation.navigate_to_cmis()
            cmis_automation.login_to_cmis()
            cmis_automation.explore_cmis_service()
        except Exception as e:
            handle_exception("CMIS", e)
        finally : 
            cmis_automation.close_browser()

        try :
            #CMIS SECOND LINK
            cmis_ocp_automation = CMISOCPAutomation()
            cmis_ocp_automation.navigate_to_cmis()
            cmis_ocp_automation.explore_cmis_service()
        except Exception as e:
            handle_exception("CMIS (OCP)", e)
        finally :
            cmis_ocp_automation.close_browser()
    else :
        update_status("CMIS_CP4BA","N/A")
        update_status("CMIS_OCP","N/A")

    if str(deployment_type).lower() == "starter" or check_cr_content.check_cr_content("enable_graph_iql: true") :
        try : 
            #Graphql
            graphql = GraphQLTester()
            graphql.run_test()
        except Exception as e:
            handle_exception("Graphql", e)
        finally :
            graphql.close_graphql()
    else :
        update_status("Graphql","N/A")

    try :
        # CPE Admin Page
        cpe_admin = CpeAdmin()
        cpe_admin.login()
        cpe_admin.navigate_to_object_store()
        cpe_admin.verify_and_capture_object_store()
        cpe_admin.navigate_to_icn_object_store_browse() #ICN Object Store Browse
        cpe_admin.css_search() #CSS Search
        cpe_admin.about() #About
        cpe_admin.navigate_to_cpe_health_check() #CPE Health Page
        cpe_admin.navigate_to_cpe_ping_page() #CPE Ping Page
        cpe_admin.navigate_to_cpe_stateless_health_check() #CPE Stateless Health Page
        cpe_admin.navigate_to_cpe_stateless_ping_page() #CPE Stateless Ping Page
    except Exception as e:
        handle_exception("CPE", e)
    finally :
        cpe_admin.close_browser()

    try :
        #CPE Filenet
        fn = Filenet()
        fn.fps_ping_page()
        fn.fps_details_page()
        fn.pe_web_services()
        fn.ce_web_services()
        fn.css_health_check()
    except Exception as e:
        handle_exception("CPE Filenet", e)
    finally :
        fn.close_filenet()

    try :
        #CPE Filenet Stateless
        fns = FilenetStateless()
        fns.Stless_FPS_ping_page()
        fns.Stless_FPS_details_page()
        fns.Stless_PE_web_services()
        fns.Stless_CE_web_services()
        fns.Stless_CSS_health_check()
        fns.close_Filenet_stateless()
    except Exception as e :
        handle_exception("CPE Filenet Stateless", e)
    finally :
        fn.close_filenet()

    try :
        #P8BPMREST
        p8bmrest = P8BPMRest()
        p8bmrest.p8bpmrest_test()
    except Exception as e :
        handle_exception("P8BPMREST", e)

    try :
        #Opensearch
        opensearch = Opensearch()
        opensearch.login_load()
    except Exception as e :
        handle_exception("Opensearch", e)
    finally :
        opensearch.close_browser()

    if "TM" in optional_components:
        try:
            #TM
            task_manager = TaskManagerPage()
            task_manager.navigate_to_task_manager()
            task_manager.take_screenshot()
        except Exception as e:
            handle_exception("TM", e)
        finally:
            task_manager.close_browser()
    else :
        update_status("TM", "N/A")

    if "IER" in optional_components:
        try:
            #IER
            ier = IERDownloader()
            ier.setup_driver()
            ier.capture_top_screen()
            ier.capture_downloads_screen()
        except Exception as e:
            handle_exception("IER", e)
        finally :
            ier.close_driver()
    else : 
        update_status("IER","N/A")
        update_status("IER_Plugin","N/A")

    if check_cr_content.check_cr_content("navigator:") :
        try :
            #Navigator Utilities
            nav_utility = NavigatorUtility()
            nav_utility.login_to_navigator()
            nav_utility.copy_cmgmt() #copy cmgmt file to nav pod using the dbauser credentials
            nav_utility.nav_event()
            nav_utility.about()
        except Exception as e:
            handle_exception("Navigator Utility", e)
        finally:
            nav_utility.close_navigator()

        try :
            #Navigator CMOD
            nav_cmod = NavigatorCMOD()
            nav_cmod.login_to_navigator()
            nav_cmod.CMOD_desktop_Search()
        except Exception as e:
            handle_exception("Navigator", e)
        finally:
            nav_cmod.close_navigator()

        try :
            #Navigator CMOD
            nav_cm8 = NavigatorCM8()
            nav_cm8.login_to_navigator()
            nav_cm8.CM8_desktop_search()
        except Exception as e:
            handle_exception("Navigator", e)
        finally:
            nav_cm8.close_navigator()
    else : 
        update_status("Navigator_desktops", "N/A")
        update_status("Navigator_Second", "N/A")
        update_status("CMOD", "N/A")
        update_status("CM8", "N/A")

    if "BAI" in optional_components:
        try :
            #BAI
            bai_automation = BaiAutomation()
            bai_automation.login()
            bai_automation.take_screenshot()
            bai_automation.nav_dashboard()
        except Exception as e:
            handle_exception("BAI", e)
        finally:
            bai_automation.close_browser()
    else : 
        update_status("BAI_Content_Dashboard","N/A")
        update_status("BAI_Navigator_Dashboard","N/A")
    try:
        fisma = Fisma()
        if fisma.check_fisma():
            fisma.fisma_main()
     
    except Exception as e :
            update_status("Fismaauditpods","N/A")
    
    try :
        #Download and check log for errors
        get_logs.logs_check()
    except Exception as e :
        handle_exception("Logs", e)
    
    try:
        #Get status from CR
        deploy_status =  DeploymentStatus()
        deploy_status.check_cr()
    except Exception as e:
        print("An error occurred while calling the script : ")
        print(str(e))

    try:
        jvm_custom_options = JvmCustomOptions()
        jvm_custom_options.verify_jvm_custom_options()
    except Exception as e:
        handle_exception("JVM Custom Options", e)

    if oc_verify == "True" :
        try:
            test_case = TestCase()
            test_case.verify_secrets()
            test_case.verify_fncm_username()
            test_case.verify_fncm_password()
            test_case.verify_fncm_secret_yaml()
            test_case.verify_iam_admin_username()
            test_case.verify_iam_admin_password()
            test_case.verify_content_app_version()
            test_case.verify_license_accepted()
            test_case.verify_cmis_status()
            test_case.verify_cdra_status()
            test_case.verify_cds_status()
            test_case.verify_cpds_status()
            test_case.verify_css_status()
            test_case.verify_cpe_status()
            test_case.verify_extshare_status()
            test_case.verify_graphql_status()
            test_case.verify_iccsap_status()
            test_case.verify_ier_status()
            test_case.verify_navigator_status()
            test_case.verify_gitgatewayService_status()
            test_case.verify_tm_status()
            test_case.verify_viewone_status()
            test_case.verify_content_operator_status()
            test_case.verify_all_end_points()
            test_case.verify_events()
            test_case.verify_pods()
            test_case.verify_storage_class()
            test_case.verify_route_cpd()
            test_case.verify_adm_top_nodes()
            test_case.verify_pv()
            test_case.verify_pvc()
            test_case.verify_result()
        except Exception as e :
            handle_exception("OC Commands Automation", e)
    else :
        logger.warning("OC commands are not executed!")
    
    #Convert html to pdf report
    try:
        pdf_report.convert_html_to_pdf()
        json_to_xml.generate_xml_report("bvt_non_admin_xml_report")
    except Exception as e :
        handle_exception("Report generation",e)

    try :
        clean.create_backup()
    except Exception as e :
        handle_exception("Creating Backup",e)

if __name__ == "__main__":
    main()
    