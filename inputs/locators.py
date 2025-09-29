class LocatorElements():
        # Login
        advanced_btn = 'details-button'
        proceedtolink = '//*[@id="proceed-link"]'
        enterpriseLDAP = 'bx--link'
        acceUsername = 'username'
        accePassword = 'password'
        loginbtn = 'loginButton'

        #ocp
        kube_login = '//a[text()="kube:admin"]'
        kube_uname = 'inputUsername'
        kube_pwd = 'inputPassword'
        kube_Admin_login = '//button[normalize-space()="Log in"]'
        installed_op = '//*[self::span or self::h1][text()="Installed Operators"]'
        installed_check = '//span[@title="Namespace"] | //td[text()="All Namespaces"]'
        cpe_init = '//dt[normalize-space()="cpe_initialized"]/following-sibling::dd//code'
        css_init = '//dt[normalize-space()="css_initialized"]/following-sibling::dd//code'
        nav_init = '//dt[normalize-space()="nav_initialized"]/following-sibling::dd//code'
        nav_bai_emitter = '//dt[normalize-space()="nav_bai_emitter_plugin_registered"]/following-sibling::dd//code'
        nav_bai_plugin = '//dt[normalize-space()="nav_bai_plugin_registered"]/following-sibling::dd//code'
        nav_app_discovery_plugin_registered = '//dt[normalize-space()="nav_app_discovery_plugin_registered"]/following-sibling::dd//code'
        nav_platform_conn_created = '//dt[normalize-space()="nav_platform_conn_created"]/following-sibling::dd//code'
        nav_platform_conn_with_context = '//dt[normalize-space()="nav_platform_conn_with_context"]/following-sibling::dd//code'
        nav_platform_plugin_registered = '//dt[normalize-space()="nav_platform_plugin_registered"]/following-sibling::dd//code'
        nav_walkme_plugin_registered = '//dt[normalize-space()="nav_walkme_plugin_registered"]/following-sibling::dd//code'
        cmis_verify = '//dt[normalize-space()="cmis_verified"]/following-sibling::dd//code'
        cpe_verify = '//dt[normalize-space()="cpe_verified"]/following-sibling::dd//code'
        css_verify = '//dt[normalize-space()="css_verified"]/following-sibling::dd//code'
        nav_verify = '//dt[normalize-space()="nav_verified"]/following-sibling::dd//code'
        name = '//input[@data-test="name-filter-input"]'
        ocp_scrollable_content = '//*[@id="content-scrollable"]'
        ocp_data = '//*[text()=\'Data\']'
        configmap_details = '//*[text()=\'ConfigMap details\']'

        # CPE
        objectstorefolder = '//span[text()="Object Stores"]'
        objectstoreselection = 'OS01'
        objectstoreselection_starter = 'CONTENT'
        administrativerfolder = '//span[text()="Administrative"]'
        indexareasfolder = 'Index Areas'
        text_search = 'IBM Text Search'
        OS01_index_area = 'OS01_index_area'
        content_index_area = 'content_index_area'
        OS01_check='//label[contains(text(),"Object store")]'
        properties = '//span[contains(@name,"objectstore.tab.Properties")]'
        property_name = '//*[text()="Property Name"]'
        properties_grid = '(//div[@class="dojoxGridScrollbox"])[2]'
        db_table_storage_location_text = '//div[contains(text(),"Database Table Storage Location")]'
        db_table_storage_location = '//input[contains(@id,"DatabaseTableStorageLocation")]'
        db_index_storage_location = '//input[contains(@id,"DatabaseIndexStorageLocation")]'
        db_lob_storage_location = '//input[contains(@id,"DatabaseLOBStorageLocation")]'
        db_schema_name = '//input[contains(@id,"DatabaseSchemaName")]'
        browsefolder = '//span[contains(text(),"Browse")]'
        rootfolder = '//span[contains(text(),"Root Folder")]'
        show_object_type_input = '//input[contains(@value,"Show Documents")]'
        folder_name = '//div[contains(text(),"Folder Name")]'
        test_folder = '//a[contains(text(),"Test_folder_auto")]'
        icnbrowse_scroll_div = '(//div[@class="dojoxGridScrollbox"])[2] | //div[contains(@id,"Folder_objectId")]//div[@class="gridxVScroller"]'
        search = '//span[text()="Search"]'
        new_obj_store_search = '//span[text()="New Object Store Search"]'
        sql_view = '//span[text()="SQL View"]'
        sql_text_area = '//textarea[contains(@id,"SQLSearchTab")]'
        sql_query = 'SELECT d.This, d.id, d.DocumentTitle FROM [Document] d inner join contentsearch c on d.this = c.queriedobject WHERE (contains(content, \'Test\'))'
        run = '//span[text()="Run"]'
        about_dropdown = '//span[@title="Tools"]'
        cpe_about = '//td[text()="About"]'
        css_search_check = '//div[text()="Object Name"]'
        health_page_check = '//*[@id="content"]'

        # Graphql
        graphql_run = '//button[contains(@title,"Execute Query")]'
        graphql_check = '//span[contains(text(), "error")]'

        # Navigator
        connections = '//span[contains(text(),"Connections")]'
        repositories = '//span[text()="Repositories"]'
        newrepositories = '//span[text()=\'New Repository\']'
        cmod = '//tr[td[@class="dijitReset dijitMenuItemLabel" and text()="Content Manager OnDemand"]]'
        cmod_iframe = '//iframe[contains(@class, "dijitBackgroundIframe")]'
        displayname = '//div[contains(@class,"dijitInputField")]//input[contains(@id,"name-field")]'
        cmodservname = '//tbody[@data-dojo-attach-point="odData"]//input[contains(@id,"server-field")]'
        connectbtn = '//span[contains(@class, "dijitButtonText") and contains(text(), "Connect...")]'
        uname = '//input[contains(@id,"username") and contains(@id,"AdminLoginDialog")]'
        passwd = '//input[contains(@id,"password") and contains(@id,"AdminLoginDialog")]'
        cmodLogInBtn = '//div[contains(@id,"AdminLoginDialog")]//span[contains(text(),"Log In") and contains(@class,"dijitButtonText")]'
        info_field = '//div[@aria-label="Information" and @aria-hidden="false"]'
        info_close_btn = '(//div[@role="dialog" and @aria-label="Information" and @aria-hidden="false"]//span[@data-dojo-attach-point="closeButtonNode"])[last()]'
        desktop_icon = '//div[text()="Desktops"]'
        new_desktop = '//span[text()="New Desktop"]'
        desktop_iframe = '//iframe[contains(@class, "dijitBackgroundIframe")]'
        platform_and_content = '//td[@class="dijitReset dijitMenuItemLabel" and normalize-space()="Platform and Content"]'
        desktop_name = '//input[contains(@id,"name-field") and contains(@id,"Desktop")]'
        desktop_connectbtn = '//input[contains(@placeholder,"Select a connection") or contains(@placeholder,"Select a repository")]'
        save_close_btn = '//span[normalize-space()="Save and Close"]'
        cm8 = '//tr[td[@class="dijitReset dijitMenuItemLabel" and text()="Content Manager"]]'
        cm8_server_field = '//tbody[@data-dojo-attach-point="cmData"]//input[contains(@id,"server-field")]'
        cmod_desktop_login_uname = '//input[contains(@id,"NavigatorMainLayout") and contains(@id,"username")]'
        cmod_desktop_login_pwd = '//input[contains(@id,"NavigatorMainLayout") and contains(@id,"password")]'
        cmod_desktop_login = '//span[contains(text(),"Log In") and contains(@id,"NavigatorMainLayout")]'
        nav_search_btn = '//td[contains(text(),"Search")]'
        cmod_search_btn = '//span[contains(text(), "FVT_PERM_TEST_PUBLIC_ACCESS")]/ancestor::*[2]//span[@data-dojo-attach-point="expandoNode"]'
        cmod_search = '//span[contains(text(),"Fake Credit Card Statements")]'
        query_search_btn = '//span[text()="Search"]'
        all_searches_btn = '//span[contains(text(), "All Searches")]/ancestor::*[2]//span[@data-dojo-attach-point="expandoNode"]'
        cm8_search = '//span[text()="TestingSave2"]'
        desktop_search_check = '//span[text()="Add Document"]'
        desktop_check = '//table[@class=\'gridxRowTable\']/tbody/tr[1]'
        cm8_login_btn = '//div[contains(@id,"AdminLoginDialog")]//span[contains(text(),"Log In") and contains(@class,"dijitButtonText")]'
        nav_about_btn = '//span[span[text()="Tools"]]'
        nav_about = '//tr[contains(@aria-label,"About")]'
        nav_about_info = '//div[@class="productVersion"]'
        navigator_slide_drawer_icon = '//div[@class="featureListIcon actions"]'
        refresh_button = '//span[text()="Refresh"]'
        navigator_Administration_option = '//tr[contains(@class, "dijitMenuItem") and contains(@aria-label, "Administration")]'
        navigator_browse_option = '//*[contains(text(),"Browse")]'
        code_event_emitter = '//span[contains(@class, "dijitTreeLabel") and text()="CodeModuleEmitter"]'
        emitter_file = '//a[contains(@class,"anchorLink") and text()="EmitterCodeModule"]'
        fncm_repo = '//tr[td[@class="dijitReset dijitMenuItemLabel" and text()="FileNet Content Manager"]]'
        server_url_field = '//tr[contains(@data-dojo-attach-point,"ServerURLRow")]//td[@class="propertyRowValue"]//input[contains(@id,"server-field")]'
        os_symbolic_name = '//tr[contains(@data-dojo-attach-point,"ObjectStoreRow")]//td[@class="propertyRowValue"]//input[contains(@id,"objectStore-field")]'
        os_display_name = '//tr[contains(@data-dojo-attach-point,"ObjectStoreDSRow")]//td[@class="propertyRowValue"]//input[contains(@id,"objectStoreDisplayName-field")]'
        iccsap_desktop = '//td[text()="ICCSAP"][1]'
        desktop_edit_button = '//span[@aria-disabled="false"]//span[contains(text(),"Edit")]'
        configuration_parameters = '//span[text()="Configuration Parameters"]'
        layout = '//div[contains(text(),"Layout")]'
        layout_scroller = '//td[@class="layoutPane"]//div[@class="gridxVScroller"]'
        iccsap_admin_feature = '//td[contains(text(),"IBM Content Collector for SAP Applications Administration Feature")]'
        iccsap_config_feature = '//td[contains(text(),"IBM Content Collector for SAP Applications Configuration Feature")]'
        iccsap_op_feature = '//td[contains(text(),"IBM Content Collector for SAP Applications Operation Feature")]'
        iccsap_admin_feature_checkbox = '//input[@aria-label="IBM Content Collector for SAP Applications Administration Feature"]'
        iccsap_config_feature_checkbox = '//input[@aria-label="IBM Content Collector for SAP Applications Configuration Feature"]'
        iccsap_op_feature_checkbox = '//input[@aria-label="IBM Content Collector for SAP Applications Operation Feature"]'
        logging_tab = '//div[text()="Logging"]'
        tm_config = '//span[text()="Task Manager Configuration"]'
        tm_enable = '//input[contains(@id, "enableTaskManager-field") and contains(@id, "TabSettings")]'
        tm_url_field = '//input[contains(@id, "taskManagerURL-field") and contains(@id, "TabSettings")]'
        tm_log_directory = '//input[contains(@id, "taskManagerLogDirectory-field") and contains(@id, "TabSettings")]'
        tm_username_field = '//input[contains(@id, "taskManagerAdminUserId-field") and contains(@id, "TabSettings")]'
        tm_password_field = '//input[contains(@id, "taskManagerAdminPassword-field") and contains(@id, "TabSettings")]'

        # BAI
        content_db_link = '//a[contains(@class, \'bai-dash__content-name\') and text()=\'Content Dashboard\']'
        bai_drop = '//div[@class="featureListIcon actions"]'
        bpc = '//td[contains(@class, "dijitMenuItemLabel") and text()="Business Performance Center"]'
        bai_xpath_locator1 = '//div[text()="Document"]'
        bai_xpath_locator2 = '//p[text()="Total number of documents"]'
        bai_xpath_locator3 = '//*[text()="timestamp" or contains(text(), "created by date")]'
        bai_xpath_locator4 = '//span[contains(text(),"ClassDescription")]'
        bai_xpath_locator5 = '//span[contains(text(),"LastModifier")]'
        bai_xpath_locator6 = '//div[contains(translate(text(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "by creator")]'
        bai_src_to_check = "./assets/images/chart/fetch_data_error.svg"
        nav_dashboard = '//a[contains(@class, \'bai-dash__content-name\') and text()=\'Navigator Dashboard\']'
        nav_xpath_locator1 = '//div[contains(text(),"action")]'
        nav_xpath_locator2 = '//div[contains(text(),"feature")]'
        nav_xpath_locator3 = '//div[contains(text(),"type")]'
        nav_xpath_locator4 = '//div[contains(text(),"user id")]'
        nav_xpath_locator5 = '//span[contains(text(),"feature")]'
        nav_xpath_locator6 = '//span[contains(text(),"action")]'
        bai_header_id = 'dashboards-header-title'
        bai_dashboard_search_id = 'search-dashboard'
        bai_dashboard_name_xpath = '//a[contains(@class, \'bai-dash__content-name\') and text()=\'[DASHBOARD_NAME]\']'
        
        #TM
        tm_verify  = '/html/body/table[1]'
        tm_ecm = '//tr[td[1]=\'ECM_PRODUCT_TYPE\']'
        
        # CMIS
        cmis_service_collection = '//*[@id="OS01_coll_display"]'
        cmis_uri_template ='//*[@id="OS01_template_display"]'
        cmis_about = '/html/body/div[2]/ul[1]/li[1]/a'
        cmis_design = '//*[@id="DESIGN_coll_display"]'
        cmis_design_template = '//*[@id="DESIGN_template_display"]'
        cmis_target = '//*[@id="TARGET_coll_display"]'
        cmis_target_template = '//*[@id="TARGET_template_display"]'
        cmis_devos = '//*[@id="DEVOS1_coll_display"]'
        cmis_devos_template = '//*[@id="DEVOS1_template_display"]'
        cmis_content = '//*[@id="CONTENT_coll_display"]'
        cmis_content_template = '//*[@id="CONTENT_template_display"]'

        #IER
        plugin = '//span[@class=\'dijitTreeLabel\' and text()=\'Plug-ins\']'
        new_plugin = '//span[@class=\'dijitReset dijitInline dijitButtonText\' and normalize-space(text())=\'New Plug-in\']'
        settings = '//span[@class=\'dijitTreeLabel\' and text()=\'Settings\']'
        p_path = '//input[contains(@id,"PluginPath-field")]'
        upload = '//tr[@data-dojo-attach-point="uploadLocalPluginRow"]//span[text()="Upload"]'
        ier_check = '//div[@rowid=\'IERApplicationPlugin\']'
        ier_plugin_path = '//input[contains(@id,"TabPlugin") and contains(@id,"fileInput")]'

        #ICCSAP
        download_done = '//*[@id="content"]'
        e1 = '//div[contains(@aria-label, \'iccsapTasks.jar\')]'
        e2 = '//div[contains(@aria-label, \'iccsapPlugin.jar\')]'

        #Filenet
        fps_ping_page = '//h1[text()=\' Process Engine Server Information (Ping Page)\']'
        fps_details_page = '/html/body/pre'
        ce_page = '/html/body'
        pe_page = '/html/body'
        css_check = '//table'

        #JAVA MAIL
        smtp_subsytem = '//span[text()="SMTP Subsystem"]'
        next_btn = '//div[contains(@id,"proxytabs_tablist_rightBtn")]'
        p8_domain = '//div[@class="ecmAdminTab"]/span[text()="P8DOMAIN"]'
        enable_email = '//input[@type="checkbox" and contains(@id,"EmailServices")]'
        smtp_hostname = '//input[@type="text" and contains(@id,"SMTPHostName")]'
        smtp_port = '//input[@type="text" and contains(@id,"SMTPPort")]'
        from_email = '//input[@type="text" and contains(@id,"DefaultFromName")]'
        to_email = '//input[@type="text" and contains(@id,"DefaultReplyToName")]'
        server_login_id = '//input[@type="text" and contains(@id,"SMTPServerLoginID")]'
        server_pwd = '//input[@type="password" and contains(@id,"SMTPServerLoginPassword")]'
        save_btn = '//span[text()="Save"]'
        send_mail = '//td[text()="Send Email"]'
        as_link = '//td[text()="As a Link"]'
        to_cell = '//td[@data-dojo-attach-point="toCell"]//input[contains(@id,"EmailDialog")]'
        subject = '//input[contains(@id,"subject")]'
        send_btn = '//span[contains(text(),"Send")]'

        #MVT Verification
        download_btn = '//span[text()="Download"]'

        #IM
        manage_users = '//div[text()="Manage users"]'
        add_users = '//*[text()="Add users"]'
        search_user = '//input[contains(@title,"Search")]'
        non_admin_user = ' //td//..//span[text()="group0001usr0002" or text()="testa1ecmuser01"]'
        next_button = '//*[contains(text(),"Next")]'
        assign_roles = '//*[text()="Assign roles directly"]'
        user_role = '//label[@for="checkbox-zen_user_role"]'
        automation_dev_role = '//label[contains(@for,"automation-developer")]'
        user_add_button = '//*[text()="Add"]'
        limited = '//*[contains(text(),"limited permissions")]'
        testa1ecmuser01_link = '//a[text()="Testa1ecmuser01" or text()="group0001usr0002"]'

        #Secrets
        secret_element = '//dt[normalize-space()="<key>"]//following-sibling::dd[1]//code'
        reveal_value_element = '//button[normalize-space()="Reveal values"]'
        
        #cpd
        menu_icon = 'sidemenu-open-icon'
        administration = 'dap-header-administer'
        access_control = 'dap-admin-users'
        add_user = 'Add-users-button-span'
        input_user_text_box = 'search-filter-search-bar'
        selected_user = "//td[contains(@id, 'add-ldap-addUsers') and contains(@id, ':username')]"
        administrator_access_ckechbox = "//label[@for='checkbox-zen_administrator_role']"
        automation_administrator_access_checkbox = "//label[@for='checkbox-iaf-automation-admin']"
        automation_analyst_access_checkbox = "//label[@for='checkbox-iaf-automation-analyst']"
        automation_developer_access_checkbox = "//label[@for='checkbox-iaf-automation-developer']"
        automation_operator_access_checkbox =  "//label[@for='checkbox-iaf-automation-operator']"
        user_access_checkbox = "//label[@for='checkbox-zen_user_role']"
        add_button = "//button[text()='Add']"

        #Navigator_multildap
        nav_menu = "featureListIcon actions"
        nav_administration = "//td[contains(@id='dijit_MenuItem') and text()='Administration']"
        nav_settings = "//span[text()='Settings']"
        nav_admin_in_settings = "//div[contains(@class, 'tabLabel') and text()='Administrators']"
        nav_input_user_text_box = "//input[contains(@id,'ecm_widget_admin_SettingAdminUsers')]"
        nav_add_button = "//span[normalize-space(text()) = 'Add']"

        #acce
        default_folder_text = '//span[text()="Folder: default"]'
        folder_security_tab = '//span[contains(@id, "folder.Security") and @class="tabLabel"]'
        security_tab = "//span[contains(@id, 'objectstore.tab.Security') and @class='tabLabel']"
        access_permissions_text = '//div[text()="Access Permissions"]'
        add_permissions = "//span[contains(text(), 'Add Permissions')]"
        add_usr_or_grp_prmsns = "//td[text()='Add User/Group Permission...']"
        user_permissions_edit_button = '//span[text()="Edit..." and contains(@id, "Security_classId_Folder")]'
        search_input_text_box = "//input[@title='search text']"
        search_button = "//span[contains(@id,'SEARCH_BTN') and text()='Search']"
        usr_to_add = "//div[@class='dijitUser']"
        right_arrow = "//span[contains(@id,'dijit_form_Button') and @title='Add']"
        permission_inheritage = '//div[contains(@id, "PERMISSION_INHERITAGE_DEPTH")]//input[contains(@value, "▼")]'
        edit_permissions = '//span[text()="Edit Permissions"]'
        object_and_all_children = '//div[contains(text(), "This object and all children")]'
        ok_button = '//span[text()="OK"]'
        save_button = "//span[contains(@id,'ObjectStore_Save') and text()='Save']"
        folder_save_button = '//span[contains(@id,"Folder_Save") and text()="Save"]'
        properties_ok_button = '//span[text()="OK"][@id="okButton_label"]'

        #ier_sanity_checks_acce
        new_object_store = "//span[text()='New']"
        object_store_display_name = "//input[contains(@id,'DisplayName_objectstore.step.Name')]"
        object_store_symbolic_name = "//input[contains(@id,'SymbolicName_objectstore.step.Name')]"
        connection = "//input[contains(@id, 'DatabaseConnection')]"
        db_schema_name = "//input[contains(@id, 'DatabaseSchemaName_objectstore')]"
        ldap_check_box = "//div[contains(@class, 'dojoxGridRowSelector') and @role='checkbox' and contains(@aria-label, 'Row 1')]"
        grant_admin_access = "//span[contains(text(),'Grant Administrative Access')]"
        add_user_or_group = "//span[contains(@id,'UsersGroups') and text()='Add User/Group Permission...']"
        search_text_box = "//input[@title='search text']"
        available_users = "//div[contains(@class, 'dojoxGridRow')]//div[contains(@class, 'dijitUser') or contains(@class, 'dijitGroup')]"
        tool_tip = "tooltipLabel"
        right_arrow_button = "//span[@role='button' and @title='Add']"
        addon_base_app_extension = "//a[contains(text(), 'Base Application Extensions')]/ancestor::div[contains(@class, 'dojoxGridRow')]//div[@role='checkbox']"
        addon_content_engine_extension = "//a[contains(text(), 'Content Engine Extensions')]/ancestor::div[contains(@class, 'dojoxGridRow')]//div[@role='checkbox']"
        addon_process_engine_extension = "//a[contains(text(), 'Process Engine Extensions')]/ancestor::div[contains(@class, 'dojoxGridRow')]//div[@role='checkbox']"
        addon_stored_search_extension = "//a[contains(text(), 'Stored Search Extensions')]/ancestor::div[contains(@class, 'dojoxGridRow')]//div[@role='checkbox']"
        addon_workplace_access_extension = "//a[contains(text(), 'Workplace Access Roles Extensions')]/ancestor::div[contains(@class, 'dojoxGridRow')]//div[@role='checkbox']"
        addon_workplace_base_extension = "//a[contains(text(), 'Workplace Base Extensions')]/ancestor::div[contains(@class, 'dojoxGridRow')]//div[@role='checkbox']"
        addon_workplace_email_extension = "//a[contains(text(), 'Workplace E-mail Extensions')]/ancestor::div[contains(@class, 'dojoxGridRow')]//div[@role='checkbox']"
        addon_workplace_form_extension = "//a[contains(text(), 'Workplace Forms Extensions')]/ancestor::div[contains(@class, 'dojoxGridRow')]//div[@role='checkbox']"
        addon_workplace_Template_extension = "//a[contains(text(), 'Workplace Templates Extensions')]/ancestor::div[contains(@class, 'dojoxGridRow')]//div[@role='checkbox']"
        addon_workplace_XT_extension = "//a[contains(text(), 'Workplace XT Extensions')]/ancestor::div[contains(@class, 'dojoxGridRow')]//div[@role='checkbox']"
        finish_button = "//span[text()='Finish']"
        close = "//span[contains(@id,'ObjectStore_Close_wizard') and text()='Close']"
        object_stores_list = "//td[contains(@class, 'gridxCell')]/a"
        workflow_system = "//td[contains(@class, 'gridxCell')]//a[contains(@id, 'WorkflowSystemName') and text()='Workflow System']"
        database_tablespace = "//label[contains(text(),'Data:')]/ancestor::td/following-sibling::td//input[contains(@id,'TXT_FIELD')]"
        admin_group = "//label[contains(text(),'Administration group:')]/ancestor::td/following-sibling::td//input[contains(@id,'TXT_FIELD')]"
        new_workflow_button = "//span[contains(@class, 'dijitButtonText') and contains(@id, 'WorkflowSystem') and text()='New']"
        input_tablespace = "//input[@class='dijitReset dijitInputInner' and @aria-required='true' and @aria-invalid='true']"
        connection_point_input = "//input[contains(@id, 'NewConnectionPoint')]"
        isolated_region_name = "//input[contains(@id, 'IsolatedRegionName')]"
        isolated_region_number = "//input[contains(@id, 'IsolatedRegionNumber')]"
        obj_close_button = "//span[text()='OS01']/ancestor::div/child::span[@title='Close' and not(@style)]"
        close_workflow = "//span[contains(@id,'WorkflowSystem_Close') and text()='Close']"
        p8domain_icon = "//span[contains(@id, 'rooticon') and text()='P8DOMAIN']"
        refresh_obj_button = "//span[text()='Refresh' and contains(@id,'ObjectStoreSet_RefreshListing')] "
        desk_appearance_tab = "//div[contains(@class, 'tabLabel') and text()='Appearance']"
        application_name_input = '//input[contains(@id, "application_name_field")]'
        desk_menus_tab = "//div[text()='Menus' and contains(@id, 'tablist') and contains(@id, 'Menus')]"
        doc_context_menu_dropdown = "//label[text()='Document context menu: ']//ancestor::td//following-sibling::td//descendant::input[@role='spinbutton']"
        doc_context_menu_declare = "//div[@role='option' and contains(text(), 'Document item context menu with Declare action')]"
        desk_workflows_tab = "//div[contains(@id, 'DesktopWorkflows') and text()='Workflows']"
        workflow_dropdown = "//input[@role='spinbutton' and contains(@aria-labelledby, '_repositories_field')]"
        workflow_option = "//label[contains(text(),'Repository:')]/parent::div/following-sibling::div/descendant::input[@role='spinbutton']"
        admin_desktop = "//td[contains(text(),'Admin Desktop')]"
        os_locator = "//a[text()='{objectstore}']"
        repo_locator = '//td[normalize-space(text())="{repo_name}"]'
        desktop_locator = '//td[normalize-space(text())="{desktop_name}"]'

        # ICCSAP Sanity Tests
        os_add_ons = '//td[contains(text(),"Add-ons")]'
        object_store_refresh = '//span[text()="Refresh" and contains(@id,"ObjectStore")]'
        root_folder_actions = '//span[text()="Actions"][contains(@id, "FolderActions")]'
        new_folder_option = '//td[text()="New Folder"][contains(@id, "FolderActions")]'
        define_new_folder = '//span[text()="Define New Folders"]'
        new_folder_name = '//input[contains(@id,"FolderName")]'
        folder_next_button = '//span[contains(@id,"Folder_Next")][contains(text(),"Next")]'
        object_properties = '//span[contains(text(),"Object Properties")]'
        specify_settings = '//span[contains(text(),"Specify Settings")]'
        create_success = '//span[text()="Success"]'
        folder_finish_button = '//span[text()="Finish" and contains(@id, "Folder_Save_wizard")]'
        folder_open_wizard = '//span[text()="Open"][contains(@id,"Folder_Open_wizard")]'
        os_check = '//span[text()="Replication Class Mappings"]'
        data_design = '//span[text()="Data Design"]'
        property_templates = '//a[text()="Property Templates"]'
        new_prop_temp = '//span[text()="New" and contains(@id,"PropertyTemplate")]'
        property_template_description = '//textarea[contains(@id,"DescriptiveText_propertytemplate")]'
        select_data_type = '//span[contains(text(),"Select the Data Type")]'
        property_template_data_type_dropdown = '//div[contains(@id,"DataType_propertytemplate")]//input[contains(@value,"▼")]'
        string_data_type = '//div[contains(text(),"String") and contains(@id,"DataType_propertytemplate")]'
        select_marketing_type = '//span[contains(text(),"Select Choice List or Marking Set")]'
        property_template_display_name = '//input[contains(@id,"DisplayName_propertytemplate")]'
        property_template_next_button = '//span[contains(@id,"PropertyTemplate_Next")][contains(text(),"Next")]'
        property_template_data_type = '//input[contains(@id,"DataType_propertytemplate")]'
        other_attributes_label = '//label[contains(text(),"Set other attributes")]'
        other_attributes = '//input[contains(@id,"otherAttributes_propertytemplate")]'
        additional_property_template = '//span[contains(text(),"Additional Property Template Attributes")]'
        max_length = '//input[contains(@id,"MaximumLengthString_propertytemplate")]'
        access_rights = '//span[contains(text(),"Access Rights")]'
        property_template_finish_button = '//span[text()="Finish" and contains(@id, "PropertyTemplate_Save_wizard")]'
        property_template_open_button = "//span[contains(@id,'PropertyTemplate_Open_wizard') and text()='Open']"
        property_template_modification_access = '//span[contains(text(),"Modification Access") and contains(@id,"PropertyTemplate")]'
        property_template_close_button = "//span[contains(@id,'PropertyTemplate_Close') and text()='Close']"
        data_design_classes = '//a[text()="Classes"]'
        document_class = '//a[text()="Document"]'
        class_definition_actions = '//span[text()="Actions"][contains(@id,"ClassDefinitionActions")]'
        new_class_option = '//td[text()="New Class"][contains(@id,"ClassDefinitionActions")]'
        name_and_describe_class = '//span[contains(text(),"Name and Describe the Class")]'
        class_display_name = '//input[contains(@id,"DisplayName_classDefinition")]'
        class_next_button = '//span[contains(@id,"ClassDefinition_Next")][contains(text(),"Next")]'
        select_and_change_object_value = '//span[contains(text(),"Select and change Object-Value properties")]'
        class_definition_finish_button = '//span[text()="Finish" and contains(@id, "ClassDefinition_Save_wizard")]'
        class_definiton_description = '//textarea[contains(@id,"DescriptiveText_classDefinition")]'
        class_open_wizard = '//span[text()="Open"][contains(@id,"ClassDefinition_Open_wizard")]'
        property_definitions = '//span[text()="Property Definitions"]'
        property_definitions_add_btn = '//span[text()="Add"]'
        property_definitions_scroller = '//div[contains(@id, "DocumentClassDefinition")]//div[@class="gridxVScroller"]'
        iccsap_error_close_btn = '//div[contains(@class, "ecmBaseDialog") and @aria-hidden="false"]//span[@title="Cancel" and @role="button"]'
        iccsap_app_configuration_feature ='//td[text()="IBM Content Collector for SAP Applications Configuration Feature"]'
        manage_collector_services = '//span[contains(text(),"Manage Collector Server Instances")]'
        import_button = '//span[contains(text(),"Import")]'
        import_input = '//input[@type="file"]'
        iccsap_error_cancel = '//div[contains(@class,"TitleBar")]//span[contains(@id,"iccsap_ICCErrorDialog")]/following-sibling::span[@title="Cancel"]'
        profile_start_button = '//span[contains(text(),"Start") and contains(@id, "iccsap_TabIccFile")]'
        iccsap_start_instace = '//span[contains(text(), "Start Instance: ICCSAP Configuration")]'
        ssl_trustore_password = '//div[contains(@id, "iccsap_widget_PasswordEntry")]//label[contains(text(), "SSL truststore")]/parent::td/following-sibling::td//input[@type="password"]'
        ssl_keystore_password = '//div[contains(@id, "iccsap_widget_PasswordEntry")]//label[contains(text(), "SSL keystore")]/parent::td/following-sibling::td//input[@type="password"]'
        user_password = '//div[contains(@id, "iccsap_widget_PasswordEntry")]//label[contains(text(), "nirenitha")]/parent::td/following-sibling::td//input[@type="password"]'
        os_password = '//div[contains(@id, "iccsap_widget_PasswordEntry")]//label[contains(text(), "P8Domain")]/parent::td/following-sibling::td//input[@type="password"]'
        ecm_widget_start = '//span[contains(@id, "ecm_widget_Button")]//span[text()="Start"]'
        daemon_message = '//p[text()="A connection to the daemon could not be established."]'
        daemon_error_close_button = '//div[contains(@id, "iccsap_ICCErrorDialog")]//span[@class="closeText"]'
        log_close_button = '//span[text()="Close" and contains(@id, "LogDisplay")]'
        not_running_status_span = '//span[text()="Running"]'
        running = '//td[contains(text(),"Running")]'
        not_running = '//td[contains(text(),"Not running")]'
        iccsap_app_administration_feature ='//td[text()="IBM Content Collector for SAP Applications Administration Feature"]'
        manage_profiles = '//span[contains(text(),"Manage Profiles")]'
        archiving_profiles = '//span[contains(text(),"Archiving Profiles")]'
        new_archiving_profile = '//span[contains(text(),"New Archiving Profile")]'
        collector_server_instance_dropdown = '//div[contains(@id, "instance")]//input[contains(@value, "▼")]'
        iccsap_config_instance = '//div[normalize-space()="ICCSAP Configuration"]'
        host_locator = '//div[text()="<host>"]'
        logical_archive_dropdown = '//div[contains(@id, "archive")]//input[contains(@value, "▼")]'
        logical_archive_option = '//div[@role="listbox" and contains(normalize-space(.), "NR (P8Domain - ICCSAPOS)")]'
        sap_document_input = '//input[contains(@id, "sapDocClass")]'
        sap_directory_input = '//input[contains(@id, "queueDirectory")]'
        archiving_profile_save_btn = '//div[contains(@id, "ArchiveProfileTab")]//span[text()="Save"]'
        archiving_profiles_tab = '//span[contains(text(),"Archiving Profiles")][contains(@id, "TabContainer")]'
        archiving_profile_locator = '//td[contains(text(),"<profile_name>")]'
        iccsap_app_operation_feature ='//td[text()="IBM Content Collector for SAP Applications Operation Feature"]'
        manage_tasks = '//span[contains(text(),"Manage Tasks")]'
        iccsap_welcome_tab = '//div[contains(@id, "iccsap_client_operator_WelcomeTab")]//div[text()= "Welcome"]'
        archiving_tasks = '//span[contains(text(),"Archiving Tasks")]'
        run_now_task_locator = '//td[contains(text(), "<task_name>")]'
        new_archiving_task = '//span[contains(text(),"New Archiving Task")]'
        task_name_field = '//input[contains(@id, "tasktitle")]'
        archiving_profile_dropdown = '//div[contains(@id, "title")]//input[contains(@value, "▼")]'
        profile_locator = '//div[contains(text(),"<profile_name>")][1]'
        archiving_profile_name = '//input[contains(@id, "ArchiveProfile") and contains(@id, "title")]'
        run_once_option = '//input[contains(@id, "run_once")]'
        run_once_date = '//input[contains(@id, "date_once") and @type="text"]'
        run_once_time = '//input[contains(@id, "time_once") and @type="text"]'
        archiving_task_save_btn = '//div[contains(@id, "ArchivingTaskTab")]//span[contains(text(), "Save")]'
        archiving_tasks_refresh_btn = '//span[contains(text(), "Refresh")][contains(@id, "ArchivingTasksTab")]'
        completed_status_locator = '//td[text()="<task_name>"]/following-sibling::td//span[contains(text(), "Completed")]'

         # CPE SANITY TESTING
        administrative_cpe_console_text = '//div[text()="IBM Administrative Console for Content Platform Engine"]'
        os01_close_button = '//span[contains(text(),"OS01") and contains(@id,"rooticon")]/ancestor::span/following-sibling::span[@title="Close"]'
        globalconfig_button = '//span[text()="Global Configuration"]'
        administration_link = '//a[text()="Administration"]'
        affinitygroups_link = '//a[text()="Affinity Groups"]'
        affgroup_link = '//a[text()="aff_group"]'
        new_button = '//span[text()="New"]'
        affinitygroup_displaynamefield = '//input[contains(@id,"CmTextSearchAffinityGroup.step.Name.HEAD")]'
        cpe_next_button = '//span[contains(text(),"Next")]'
        aff_display_name_heading = '//td[text()="Display name"]'
        finish_button = '//span[text()="Finish"]'
        success_text = '//span[text()="Success"]'
        close_button = '//span[text()="Close"]'
        refresh_aff_button = '//span[text()="Refresh"and contains(@id,"CmTextSearchAffinityGroupSet_label")]'
        affinity_close_button = '//span[contains(text(),"Affinity Gr")]/ancestor::span/following-sibling::span[@title="Close"]'
        affinity_action_button = '//span[contains(text(),"Actions")]'
        delete_affinity_button = '//td[contains(text(),"Delete Affinity Group")]'
        administration_close_button = '//span[contains(text(),"Adminis")]/ancestor::span/following-sibling::span[@title="Close"]'
        global_close_button = '//span[contains(text(),"Global")]/ancestor::span/following-sibling::span[@title="Close"]'


        object_store = '//span[text()="Object Stores"]'
        object_store_OS01_icon = '//span[contains(@id,"TreeNode")and text()="OS01"]'
        object_store_name = '//a[text()="OS01"]'
        events_actions_processes = '//span[text()="Events, Actions, Processes"]'
        change_processor_action_link = '//a[text()="Change Preprocessor Actions"]'
        change_processor_action_class_text = '//span[text()="Specify the Change Preprocessor Action Class"]'
        processor_newbutton = '//span[text()="New" and contains(@id,"CmChangePreprocessorActionSet_label")]'
        processor_display_name_heading_textfield = '//input[contains(@id,"DisplayName_.step.Name")]'
        processor_description_textfield = '//textarea[contains(@id,"DescriptiveText_.step.Name")]'
        processor_specify_type_text = '//span[text()="Specify the Type of Change Preprocessor Action"]'
        processor_checbox_disabled = '//input[contains(@id,"sEnabled_cmChangePreprocessorAction.step.ActionType.HEAD") and @aria-checked="false"]'
        processor_checkbox = '//input[contains(@id,"IsEnabled_cmChangePreprocessorAction.step.ActionType.HEAD")]'
        processor_status_checkbox = '//input[contains(@id,"sEnabled_cmChangePreprocessorAction.step.ActionType.HEAD")]'
        processor_objectproperties_text = '//span[text()="Object Properties"]'
        processor_javascript_radiobutton = '//label[contains(text(),"JavaScript")]/ancestor::td/preceding-sibling::td/descendant::input'
        processor_javascript_data = '//textarea[contains(@id,"ScriptText_cmChangePreprocessorAction.step.ActionScript")]'
        processor_changepreprocessor_close = '//span[contains(text(),"Change Pre")]/ancestor::span/following-sibling::span[@title="Close"]'
        processor_events_close = '//span[contains(text(),"Events")]/ancestor::span/following-sibling::span[@title="Close"]'
        processor_action_button = '//span[contains(@id, "CmChangePreprocessorAction") and text()="Actions"]'
        processor_action_delete_button = '//td[text()="Delete Change Preprocessor Action"]'

        bsct_datadesign_button = '//span[text()="Data Design"]'
        bsct_background_search_class_template_button = '//a[text()="Background Search Class Templates"]'
        bsct_new_button ='//span[text()="New" and contains(@id,"BackgroundSearches")]'
        bsct_displayname_textfield = '//input[contains(@id,"DisplayName_backgroundSearchTemplate.step.Name.HEAD")]'
        bsct_symbolic_name_textfield = '//input[contains(@id,"SymbolicName_backgroundSearchTemplate.step.Name.HEAD")]'
        bsct_search_expression_textfield = '//textarea[contains(@id,"SearchExpression_backgroundSearchTemplate.step.SearchExpression.HEAD")]'
        bsct_set_search_option = '//span[text()="Set Search Options"]'
        bsct_decide_new_existing_class = '//span[text()="Decide to Use a New or Existing Search Result Class"]'
        bsct_name_the_search_result_class = '//span[text()="Name the Search Result Class"]'
        bsct_define_search_result_prop ='//span[text()="Define Search Result Properties"]'
        bsct_summary = '//span[text()="Summary"]'
        bsct_close_button = '//span[contains(text(),"Background")]/ancestor::span/following-sibling::span[@title="Close"]'
        bsct_datadesign_close = '//span[contains(text(),"Data Design")]/ancestor::span/following-sibling::span[@title="Close"]'
        bsct_action_button = '//span[contains(@id,"acce.action.BackgroundSearch") and text()="Actions"]'
        bcst_delete_button = '//td[contains(@id,"acce.action.BackgroundSearch") and text()="Delete"]'

        choice_list_link = '//a[text()="Choice Lists"]'
        choice_new_button = '//span[text()="New" and contains(@id,"ChoiceList_label")]'
        choice_display_name_textfield = '//input[contains(@id,"DisplayName_choiceList.step.Name.HEAD")]'
        choice_description_textfield = '//textarea[contains(@id,"DescriptiveText_choiceList.step.Name.HEAD")]'
        choice_next_button = '//span[contains(text(),"Next") and contains(@id,"ChoiceList_NextStep")]'
        choice_select_text = '//span[text()="Select Data Types"]'
        choice_new_group = '//span[contains(text(),"New Groups")]'
        choice_new_display_name = '//input[contains(@id,"DISPLAYTEXTAREA")]'
        choice_add_button = '//span[text()="Add"]'
        choice_ok_button = '//span[@id="okButton"]'
        choice_new_item = '//span[text()="New Items"]'
        choice_close_button = '//span[contains(text(),"Choice List")]/ancestor::span/following-sibling::span[@title="Close"]'
        choice_action_button = '//span[contains(@id,"action.GroupActions_classId_ChoiceList") and text()="Actions"]'
        choice_delete_button = '//td[contains(@id,"action.DeleteChoiceList.HEAD") and text()="Delete Choice List"]'
        choice_choiceitems_button = '//span[text()="Choice Items"]'
        choice_list_created_close = '//span[text()="Close" and contains(@id,"ChoiceList_Close_wizard")]'
        choice_list_finish_button = '//span[text()="Finish" and contains(@id,"ChoiceList_Save_wizard")]'
        choice_list_assignchoice_checkbox = '//input[contains(@id,"SelectChoiceList_propertytemplate")]'
        choice_list_selectall = '//span[contains(@id,"FN_MODIFIEDACCESS") and text()="Select All"]'
        choice_list_search_filter = '//input[contains(@id,"filter_text_classId_ObjectStore")]'
        
        object_store_OS01_root_icon = '//span[contains(@id,"rooticon") and text()="OS01"]'
        subfolder_browser = '//span[text()="Browse"]'
        subfolder_root_folder = '//a[text()="Root Folder"]'
        subfolder_action_button = '//span[contains(@id,"acce.action.FolderActions_classId_Folder") and text()="Actions"]'
        subfolder_newfolder_button = '//td[contains(@id,"acce.action.FolderActions_NewFolder") and text()="New Folder"]'
        subfolder_foldername_textfield = '//input[contains(@id,"FolderName_folder.step.Name.Folder.HEAD")]'
        subfolder_next_button = '//span[contains(text(),"Next") and contains(@id,"Folder_NextStep")]'
        subfolder_object_properties = '//span[text()="Object Properties"]'
        subfolder_retaining_prop = '//span[text()="Specify Settings for Retaining Objects"]'
        subfolder_open_button = '//span[text()="Open"]'
        subfolder_close_root_folder = '//span[contains(text(),"Root Folder")]/ancestor::span/following-sibling::span[@title="Close"]'
        subfolder_properties_button = '//span[text()="Properties" and contains(@id,"folder.Properties_acce.element.tab.Properties")]'
        subfolder_action_delete_button = '//td[contains(@id,"action.FolderActions_Delete") and text()="Delete"]'
        subfolder_browser_close_button = '//span[contains(text(),"Browse")]/ancestor::span/following-sibling::span[@title="Close"]'
        subfolder_deletefolder_text = '//span[text()="Delete Folder"]'


        instance_browser_expand = '//span[text()="Browse"]/ancestor::div/child::span[@data-dojo-attach-point="expandoNode"]'
        instance_rootfolder_expand = '//span[text()="Root Folder"]/ancestor::div/child::span[@data-dojo-attach-point="expandoNode"]'
        instance_copyobjectstore = '//td[contains(@id,"CopyObjectReference_contextual") and text()="Copy Object Reference"]'
        instance_rootfolder = '//span[text()="Root Folder"]'
        instance_classes = '//a[text()="Classes"]'
        instance_folder = '//span[text()="Folder"]'
        instance_createinstance_button = '//td[text()="Create Instance"]'
        instance_parent_dropdown = '//img[@id="contextMenu-2"]'
        instance_dropdown_paste = '//table[contains(@class,"dijitMenuSelected dijitSelected")]/descendant::td[text()="Paste Object"]'
        instance_parent_textfield = '//input[contains(@id,"FolderName_object_step_Title_HEAD")]'
        instance_close_button = '//span[contains(@id,"ClassDefinition_Close_wizard") and text()="Close"]'
        instance_datadesign_expand = '//span[text()="Data Design"]/ancestor::div/child::span[@data-dojo-attach-point="expandoNode"]'
        instance_classes_expand = '//span[text()="Classes"]/ancestor::div/child::span[@data-dojo-attach-point="expandoNode"]'
        instance_delete_heading = '//span[text()="Delete Folder" and @role="heading"]'
        instance_delete_button = '//table[contains(@class,"dijitMenuSelected dijitSelected")]/descendant::td[text()="Delete"]'
        instance_folder_action = '//span[contains(@id,"action.FolderActions") and text()="Actions"]'
        instance_folder_delete = '//td[contains(@id,"action.FolderActions_Delete") and text()="Delete"]'
        instance_next_button = '//span[contains(@id,"NextStep_wizard") and contains(text(),"Next")]'

        document_doc_button = '//span[text()="Document"]'
        document_doc_action_button = '//span[contains(@id,"acce.action.ClassDefinitio") and text()="Actions"]'
        document_general_tab = '//span[contains(@id,"acce.element.tab.ClassDefinitionGeneral") and text()="General"]'
        document_newclass_button = '//td[contains(@id,"acce.action.ClassDefinitionActions_NewClass") and text()="New Class"]'
        document_displayname_textfield = '//input[contains(@id,"DisplayName_classDefinition")]'
        document_symbolicname_textfield = '//input[contains(@id,"SymbolicName_classDefinition")]'
        document_objectvalue_text = '//span[text()="Select and change Object-Value properties"]'
        document_close_button = '//span[contains(@id,"admin.ClassDefinition_Close_wizard") and text()="Close"]'
        document_open_button = '//span[contains(@id,"com.filenet.api.admin.ClassDefinition_Open_wizard") and text()="Open"]'
        document_newdoc_close = '//span[contains(text(),"DOC")]/ancestor::span/following-sibling::span[@title="Close"]'
        document_doc_close = '//span[contains(text(),"Document")]/ancestor::span/following-sibling::span[@title="Close"]'
        document_doc_expand = '//span[text()="Document"]/ancestor::div/child::span[@data-dojo-attach-point="expandoNode"]'
        document_folder_button = '//span[text()="Folder"]'
        document_folder_close = '//span[contains(text(),"Folder")]/ancestor::span/following-sibling::span[@title="Close"]'
        document_newfolder_close = '//span[contains(text(),"NewFolder")]/ancestor::span/following-sibling::span[@title="Close"]'
        document_doc_delete_button = '//td[contains(@id,"acce.action.ClassDefinitionActions_Delete") and text()="Delete"]'
        document_admin_text = '//span[text()="Administration Console for Content Platform Engine"]'
        document_folder_expand = '//span[text()="Folder"]/ancestor::div/child::span[@data-dojo-attach-point="expandoNode"]'

        markingset_button = '//a[text()="Marking Sets"]'
        markingset_datadesign_button = '//a[text()="Data Design"]'
        markingset_display_button = '//input[contains(@id,"DisplayName_markingset.step.Name")]'
        markingset_description_textarea = '//textarea[contains(@id,"DescriptiveText_markingset.step.Name")]'
        markingset_checkbox = '//input[contains(@id,"IsHierarchical_markingset.step.Name")]'
        markingset_next_button = '//span[contains(@id,"MarkingSet_NextStep") and contains(text(),"Next")]'
        markingset_new_create_button = '//span[text()="New" and contains(@id,"MarkingSetSet")]'
        markingset_new_button = '//span[contains(@id,"ACTIONADD") and contains(text(),"New")]'
        markingset_value_text = '//span[text()="Name and Configure the Marking Values"]'
        markingset_ok_button = '//span[@id="okButton_label"]'
        markingset_markingvalue_textfield = '//input[contains(@id,"MARKING_VALUE")]'
        markingset_administration_text = '//span[text()="Administration Console for Content Platform Engine"]'
        markingset_admin_ok_button = '//span[contains(@id,"firstButton") and text()="OK"]'
        markingset_open_button = '//span[text()="Open" and  contains(@id,"MarkingSet_Open_wizard")]'
        markingset_close_button = '//span[contains(text(),"Marking")]/ancestor::span/following-sibling::span[@title="Close"]'
        markingset_action_button = '//span[contains(text(),"Actions") and contains(@id,"action.GroupActions")]'
        markingset_delete_button = '//td[text()="Delete Marking Set"]'

        subscription_doc_close = '//span[contains(text(),"Document")]/ancestor::span/following-sibling::span[@title="Close"]'
        subscription_action_button = '//span[text()="Actions" and contains(@id,"acce.action.ClassDefinitionActions")]'
        subscription_new_subscription = '//td[contains(text(),"New Subscription") and contains(@id,"action.ClassDefinitionActions")]'
        subscription_displayname = '//input[contains(@id,"DisplayName_subscription")]'
        subscription_description = '//textarea[contains(@id,"DescriptiveText_subscription")]'
        subscription_specify_text = '//span[contains(text(),"Specify the Subscription Behavior")]'
        subscription_next_button = '//span[contains(text(),"Next") and contains(@id,"Subscription_NextStep_wizard")]'
        subscription_deletion_checkbox= '//td[text()="Deletion Event"]/preceding-sibling::td'
        subscription_uparrow = '//div[text()="Event Name"]/preceding-sibling::div[@class="dojoxGridArrowButtonNode"]'
        subscription_update_even_checkbox = '//td[text()="Update Event"]/preceding-sibling::td'
        subscription_event_new_button = '//span[contains(text(),"New") and contains(@id,"wizard_addbutton")]'
        subscription_event_displayname = '//input[contains(@id,"DisplayName_eventAction")]'
        subscription_event_descriptionname= '//textarea[contains(@id,"DescriptiveText_eventAction")]'
        subscription_event_nextbutton = '//span[contains(text(),"Next") and contains(@id,"EventAction_NextStep_wizard")]'
        subscription_event_actiontype_text = '//span[contains(text(),"Event Action Type Selection")]'
        subscription_event_action_script_text = '//span[text()="Enter the Event Action Script"]'
        subscription_event_finish_button = '//span[text()="Finish" and contains(@id,"EventAction_Save_wizard")]'
        subscription_event_close_button = '//span[text()="Close" and contains(@id,"EventAction_Close_wizard")]'
        subscription_additionaloption_text  = '//span[text()="Specify Additional Options"]'
        subscription_runsynchronize_checkbox = '//input[contains(@id,"AdditionalPropSynchronous_subscription_AdditionalProperties")]'
        subscription_open_button = '//span[text()="Open" and contains(@id,"Subscription_Open_wizard")]'
        subscription_post_action_button = '//span[text()="Actions"and contains(@id,"SubscriptionActions")]'
        subscription_post_delete_button = '//td[text()="Delete"and contains(@id,"SubscriptionActions")]'
        subscription_post_event_deletion_text = '//div[contains(text(),"Do you want to delete subscription")]'
        subscription_event_deletion_checkbox = '//input[contains(@id,"ClassSubscription") and @role="checkbox"]'
        subscription_event_action_text = '//span[contains(text(),"Select an Event Action")]'
        subscription_runmode_checkbox = '//div[contains(@widgetid,"AdditionalPropSynchronous_subscription_AdditionalProperties")]'
        subscription_docfile_close_button = '//span[text()="Close" and contains(@id,"ClassDefinition_Close")]'
        subscription_eventaction_dropdown = '//input[contains(@id,"eventAction_eventAction.step.eventType.HEAD")]'

        lifecycle_event_action_expand = '//span[text()="Events, Actions, Processes"]/ancestor::div/child::span[@data-dojo-attach-point="expandoNode"]'
        lifecycle_defect_life_cycle_action_button = '//span[text()="Document Lifecycle Actions"]'
        lifecycle_new_button = '//span[text()="New" and contains(@id,"DocumentLifecycleActionSet_New")]'
        lifecyle_display_textfield = '//input[contains(@id,"DisplayName_documentLifecycleAction")]'
        lifecycle_description_textarea = '//textarea[contains(@id,"DescriptiveText_documentLifecycleAction")]'
        lifecycle_next_button = '//span[contains(text(),"Next") and contains(@id,"DocumentLifecycleAction_NextStep")]'
        lifecycle_specify_documentation_text = '//span[contains(text(),"Specify the Type of Documentation Lifecycle Action")]'
        lifecycle_enter_the_doc_text = '//span[text()="Enter the Documentation Lifecycle Action Script"]'
        lifecycle_finish_button = '//span[text()="Finish"and contains(@id,"DocumentLifecycleAction_Save_wizard")]'
        lifecycle_open_button = '//span[text()="Open"and contains(@id,"DocumentLifecycleAction_Open_wizard")]'
        lifecycle_action_button = '//span[text()="Actions" and contains(@id,"DocumentLifecycleAction")]'
        lifecycle_delete_button = '//td[text()="Delete Document Lifecycle Action"]'
        lifecycle_ok_button = '//span[text()="OK" and contains(@id,"firstButton")]'
        lifecycle_java_handler_text = '//div[text()="The Java class handler cannot be left blank."]'

        custom_object_actions_button = '//span[contains(text(),"Actions") and contains(@id,"action.FolderActions")]'
        custom_object_new = '//td[text()="New Custom Object" and contains(@id,"action.FolderActions")]'
        custom_object_containment_name_textfield = '//input[contains(@id,"ontainmentName_folder.step.Name")]'
        custom_object_next_button = '//span[contains(@id,"CustomObject_NextStep_wizard") and contains(text(),"Next")]'
        custom_object_retaining_option_text = '//span[text()="Specify Settings for Retaining Objects"]'
        custom_object_close_button = '//span[text()="Close" and contains(@id,"CustomObject_Close")]'
        custom_object_security_policy = '//span[text()="Security Policy" and contains(@id,"CustomObject")]'
        custom_object_security_policy_name_field = '//input[contains(@id,"SEC_POLICY_TAB_NAME_LIST")]'
        custom_object_security_policy_apply_button = '//span[contains(@id,"SEC_POLICY_TAB_ACTION_APPLY") and text()="Apply"]'
        

        property_template_link = '//span[text()="Property Templates"]'
        property_template_prop_close = '//span[contains(text(),"Property")]/ancestor::span/following-sibling::span[@title="Close"]'
        property_template_search_button = '//input[contains(@id,"DataDesignobjectstore.PropertyTemplate")]'
        property_template_filter_button = '//span[text()="Filter"]'
        property_template_action_button = '//span[text()="Actions"and contains(@id,"PropertyTemplateObject")]'
        property_template_property_delete = '//td[text()="Delete Property Template"]'
        property_template_object_dropdown = '//div[contains(text(),"Object") and contains(@id,"DataType_propertytemplate")]'
        property_template_single_multi_text = '//span[text()="Single or Multi-Value?"]'
        property_template_classes_button = '//span[text()="Classes"]'
        property_template_property_definition_tab = '//span[text()="Property Definitions"]'
        property_template_add_button = '//span[text()="Add" and contains(@id,"PropertyDefinition")]'
        property_template_propertydefinition_searchtab = '//input[contains(@id,"filterPropertyDefinitions")]'
        property_template_more_button = '//span[text()="More"]'
        property_template_requiredclass_field = '//input[contains(@id,"RequiredClassId__Property")]'
        property_template_view_properites_dropdown = '//td[text()="View all properties"]'
        property_template_savebutton = '//span[text()="Save" and contains(@id,"SaveButton__Property")]'
        property_template_close_doc = '//span[text()="Close" and contains(@id,"ClassDefinition_Close")]'
        property_template_classes_close_button = '//span[contains(text(),"Classes")]/ancestor::span/following-sibling::span[@title="Close"]'
        property_template_data_type_drop = '//input[contains(@id,"DataType_propertytemplate.step.DataType.HEAD")]'

        


        security_policy = '//a[text()="Security Policies"]'
        security_policy_new_button = '//span[text()="New" and contains(@id,"SecurityPolicySet_New_local")]'
        security_policy_displayname = '//input[contains(@id,"DisplayName_securityPolicy")]'
        security_policy_next_button = '//span[contains(text(),"Next") and contains(@id,"SecurityPolicy_NextStep")]'
        security_policy_specify_template_text = '//span[text()="Specify the Security Templates"]'
        security_policy_existing = '//a[text()="TestSecurityPolicy"]'
        secruity_policy_close = '//span[contains(text(),"Security")]/ancestor::span/following-sibling::span[@title="Close"]'
        security_policy_admin_close = '//span[contains(text(),"Administ")]/ancestor::span/following-sibling::span[@title="Close"]'
        security_policy_add_button = '//span[contains(text(),"Add") and contains(@id,"FN_ST_ACTIONADD")]'
        security_policy_add_security_template_text = '//span[text()="Add Security Templates"]'
        security_policy_released_checkbox = '//div[text()="Released"]/parent::td/preceding-sibling::td/descendant::input[contains(@id,"FN_AST_FIELDID")]'
        security_policy_reservation_checkbox = '//div[text()="Reservation"]/parent::td/preceding-sibling::td/descendant::input[contains(@id,"FN_AST_FIELDID")]'
        security_policy_inprocess_checkbox = '//div[text()="In Process"]/parent::td/preceding-sibling::td/descendant::input[contains(@id,"FN_AST_FIELDID")]'
        security_policy_superseded_checkbox = '//div[text()="Superseded"]/parent::td/preceding-sibling::td/descendant::input[contains(@id,"FN_AST_FIELDID")]'
        security_policy_ok_button = '//span[text()="OK" and contains(@id,"FN_AST_ACTIONOK")]'
        security_policy_tab = '//span[text()="Security Policy" and contains(@id,"classId_CustomObject")]'
        security_policy_add_name = '//input[contains(@id,"FN_SEC_POLICY_TAB_NAME_LIST")]'
        security_policy_apply_button = '//span[contains(@id,"SEC_POLICY_TAB_ACTION_APPLY") and text()="Apply"]'
        security_policy_released_radiobutton = '//td[text()="Released"]/preceding-sibling::td//div[contains(@id,"FN_SEC_POLICY_TAB_SEC_TEMPLATES_GRID")]'
        security_policy_save_button = '//span[text()="Save" and contains(@id,"ustomObject_Save")]'
        security_policy_save_verification = '//span[@title="Save" and @aria-disabled="true" and contains(@id,"CustomObject_Save_local")]'
        security_policy_created = '//input[@value="TestSecurityPolicy" and contains(@id,"FN_SEC_POLICY_TAB_NAME_LIST")]'


        
        






        


        #Fisma
        # datsesign_node = '//span[text()="Data Design"]/../..//span[@data-dojo-attach-point="expandoNode"]'
        datsesign_node = '//span[normalize-space(text())="Data Design"]/ancestor::div[1]//span[@data-dojo-attach-point="expandoNode"]'
        # class_tab = '//span[text()="Classes"]/../..//span[@data-dojo-attach-point="expandoNode"]'
        class_tab = '//span[text()="Classes"]/ancestor::div[1]//span[@data-dojo-attach-point="expandoNode"]'
        document_tab = '//span[text()="Document"]'
        class_def = '//div[contains(@id,"proxytabs_tablist_rightBt") and contains(@id,"classId_DocumentClassDefinition_objectId") ]'
        rightarrow_btn = '//div[contains(@id, "_proxytabs_tablist_rightBtn")]'
        audit_def = '//span[text()="Audit Definitions"]'
        new_btn1 = '//span[text()="New"]'
        display_name = '//input[contains(@id,"DisplayName")]'
        sym_name  = '//input[contains(@id,"event")]'
        data_design = '//span[text()="Data Design"]'
        class_text = '//a[text()="Classes"]'
        document_text = '//a[text()="Document"]'
        new_btn = '//span[contains(@widgetid,"FN_CLASSDEFINITIONAUDITDEFINITIONS_AD_BTNNEW_classId_DocumentClassDefinition_objectId")]'

        fisma_def_title='//input[contains(@id, "displayName")]'

        # fisma_def_title = '//label[text()="Display name: "]/../../following-sibling::td[1]/div/div/input'
        recording_level = '//input[contains(@id, "objectStateRecordingLevel")]'
        audit_success = '//input[contains(@id,"auditSuccess") and (@type="checkbox")]'
        audit_fail = '//input[contains(@id,"auditFailure") and (@type="checkbox")]'
        apply_subclass = '//input[contains(@id,"applySubclasses") and (@type="checkbox")]'
        fisma_enabled = '//input[contains(@id,"isEnabled") and (@type="checkbox")]'
        save_btn =  '//span[contains(@id, "ClassDefinition_Save_local_classId_DocumentClassDefinition") and (text()="Save")]/../../..'
        audit_edit = '//input[contains(@id,"AuditLevel_objectstore")]'
        audit_save = '//span[contains(@widgetid,"com.filenet.api.core.ObjectStore_Save_local_classId_ObjectStore")]'
        audit_save_btn = '//span[contains(@widgetid,"com.filenet.api.admin.ClassDefinition_Save_local_classId")]'
        doc_root_folder = "//a[contains(text(),'Root Folder')]"
        actions_button = "//span[contains(@id,'acce.action.FolderActions') and contains(text(),'Actions')]"
        new_doc_option = '//td[text()="New Document"][contains(@id, "FolderActions")]'
        doc_title = "//input[contains(@id, 'DocumentTitle_folder')]"
        new_doc_next_button = "//span[contains(@id, 'Document_NextStep_wizard') and contains(text(),'Next')]"
        with_content_checkbox = "//input[contains(@id, 'WithContent_folder.step.Name.Document')]"