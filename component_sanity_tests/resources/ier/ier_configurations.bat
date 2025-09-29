@echo off
echo ==========================================
echo Starting IER Profile Configuration...
echo ==========================================

:: Step 0: Set Variables
set "ce_wsi_url=<CE_WSI_URL>"
set "ldap_username=<LDAP_USERNAME>"
set "datamodel_type=Base"
set "gcd_password=<LDAP_PASSWORD>"
set "fileplan_object_store_name=FPOS"
set "include_nara_option=false"
set "record_object_store_name=ROS"
set "include_classified_option=false"
set "can_declare_value=Document"
set "connection_point_name=PECN"
set "navigator_url=<NAVIGATOR_URL>"
set "object_store_connection=FPOS"
set "reconfigure_workflows=false"
set "transfer_fpos=FPOS"
set "retransfer_flag=false"
set "cesweep_os=FPOS"

:: Step 1: Go to the configuration directory
cd /d "C:\Program Files\IBM\EnterpriseRecords\configure"

:: Step 2: Run the generateConfig command
configmgr_cl.exe generateConfig -profiletype objectstore_configuration -profile "C:\Program Files\IBM\EnterpriseRecords\configure\profiles\object_store_configuration_profile" -silent -debug

echo.
echo Profile generation complete!

:: Step 3: Switch to the profile directory
cd /d "C:\Program Files\IBM\EnterpriseRecords\configure\profiles\object_store_configuration_profile"
echo Switched to profile directory!

:: Step 4: Update EnvironmentObjectStoreConfiguration.xml
echo Updating environmentObjectStoreConfiguration.xml ...
powershell -Command "$xml = [xml](Get-Content 'EnvironmentObjectStoreConfiguration.xml'); ($xml.configuration.property | Where-Object { $_.name -eq 'ContentEngineWSIURL' }).value = '%ce_wsi_url%'; ($xml.configuration.property | Where-Object { $_.name -eq 'ContentEngineAdministratorUsername' }).value = '%ldap_username%'; ($xml.configuration.property | Where-Object { $_.name -eq 'ContentEngineAdministratorPassword' }).value = '%gcd_password%'; $xml.Save('EnvironmentObjectStoreConfiguration.xml')"

:: Step 5: Run EnvironmentObjectStoreConfiguration.xml
echo Running EnvironmentObjectStoreConfiguration.xml ...
"C:\Program Files\IBM\EnterpriseRecords\configure\configmgr_cl.exe" execute -profile "C:\Program Files\IBM\EnterpriseRecords\configure\profiles\object_store_configuration_profile" -taskfile EnvironmentObjectStoreConfiguration.xml

:: Step 6: Update createMarkingSetsAndAddOns.xml
echo Updating createMarkingSetsAndAddOns.xml ...
powershell -Command "$xml1 = [xml](Get-Content 'createMarkingSetsAndAddOns.xml'); ($xml1.configuration.property | Where-Object { $_.name -eq 'ContentEngineGCDAdministrator' }).value = '%ldap_username%'; ($xml1.configuration.property | Where-Object { $_.name -eq 'ContentEngineGCDPassword' }).value = '%gcd_password%'; ($xml1.configuration.property | Where-Object { $_.name -eq 'Datamodel' }).value = '%datamodel_type%'; $xml1.Save('createMarkingSetsAndAddOns.xml')"

:: Step 7: Run createMarkingSetsAndAddOns.xml
echo Running createMarkingSetsAndAddOns.xml ...
"C:\Program Files\IBM\EnterpriseRecords\configure\configmgr_cl.exe" execute -profile "C:\Program Files\IBM\EnterpriseRecords\configure\profiles\object_store_configuration_profile" -taskfile createMarkingSetsAndAddOns.xml

:: Step 8: Update configureFPOS.xml
echo Updating configureFPOS.xml ...
powershell -Command "$xml2 = [xml](Get-Content 'configureFPOS.xml'); ($xml2.configuration.property | Where-Object { $_.name -eq 'ContentEngineObjectStore' }).value = '%fileplan_object_store_name%'; ($xml2.configuration.property | Where-Object { $_.name -eq 'Datamodel' }).value = '%datamodel_type%'; ($xml2.configuration.property | Where-Object { $_.name -eq 'IncludeNaraOption' }).value = '%include_nara_option%'; $xml2.Save('configureFPOS.xml')"

:: Step 9: Run configureFPOS.xml
echo Running configureFPOS.xml ...
"C:\Program Files\IBM\EnterpriseRecords\configure\configmgr_cl.exe" execute -profile "C:\Program Files\IBM\EnterpriseRecords\configure\profiles\object_store_configuration_profile" -taskfile configureFPOS.xml

:: Step 10: Update configureROS.xml
echo Updating configureROS.xml ...
powershell -Command "$xml3 = [xml](Get-Content 'configureROS.xml'); ($xml3.configuration.property | Where-Object { $_.name -eq 'ContentEngineObjectStore' }).value = '%record_object_store_name%'; ($xml3.configuration.property | Where-Object { $_.name -eq 'IncludeClassifiedDocumentOption' }).value = '%include_classified_option%'; ($xml3.configuration.property | Where-Object { $_.name -eq 'CanDeclareSelection' }).value = '%can_declare_value%'; $xml3.Save('configureROS.xml')"

:: Step 11: Run configureROS.xml
echo Running configureROS.xml ...
"C:\Program Files\IBM\EnterpriseRecords\configure\configmgr_cl.exe" execute -profile "C:\Program Files\IBM\EnterpriseRecords\configure\profiles\object_store_configuration_profile" -taskfile configureROS.xml

:: Step 12: Update configureWorkflows.xml
echo Updating configureWorkflows.xml ...
powershell -Command "$xml4 = [xml](Get-Content 'configureWorkflows.xml'); ($xml4.configuration.property | Where-Object { $_.name -eq 'ConnectionPoint' }).value = '%connection_point_name%'; ($xml4.configuration.property | Where-Object { $_.name -eq 'IERWorkflowConfigurationDirectory' }).value = 'C:\Program Files\IBM\EnterpriseRecords\Workflow\configureRMworkflow'; ($xml4.configuration.property | Where-Object { $_.name -eq 'CEPEUser' }).value = '%ldap_username%'; ($xml4.configuration.property | Where-Object { $_.name -eq 'CEPEUserPassword' }).value = '%gcd_password%'; ($xml4.configuration.property | Where-Object { $_.name -eq 'ICNWebApplicationURL' }).value = '%navigator_url%'; ($xml4.configuration.property | Where-Object { $_.name -eq 'ObjectStoreConn' }).value = '%object_store_connection%'; ($xml4.configuration.property | Where-Object { $_.name -eq 'Reconfigureorkflows' }).value = '%reconfigure_workflows%'; $xml4.Save('configureWorkflows.xml')"

:: Step 13: Run configureWorkflows.xml
echo Running configureWorkflows.xml ...
"C:\Program Files\IBM\EnterpriseRecords\configure\configmgr_cl.exe" execute -profile "C:\Program Files\IBM\EnterpriseRecords\configure\profiles\object_store_configuration_profile" -taskfile configureWorkflows.xml

:: Step 14: Update transferWorkflows.xml
echo Updating transferWorkflows.xml ...
powershell -Command "$xml5 = [xml](Get-Content 'transferWorkflows.xml'); ($xml5.configuration.property | Where-Object { $_.name -eq 'FilePlanObjectStore' }).value = '%transfer_fpos%'; ($xml5.configuration.property | Where-Object { $_.name -eq 'ConnectionPoint' }).value = '%connection_point_name%'; ($xml5.configuration.property | Where-Object { $_.name -eq 'RetransferWorkflows' }).value = '%retransfer_flag%'; $xml5.Save('transferWorkflows.xml')"

:: Step 15: Run transferWorkflows.xml
echo Running transferWorkflows.xml ...
"C:\Program Files\IBM\EnterpriseRecords\configure\configmgr_cl.exe" execute -profile "C:\Program Files\IBM\EnterpriseRecords\configure\profiles\object_store_configuration_profile" -taskfile transferWorkflows.xml

:: Step 16: Update configureContentEngineSweep.xml
echo Updating configureContentEngineSweep.xml ...
powershell -Command "$xml6 = [xml](Get-Content 'configureContentEngineSweep.xml'); ($xml6.configuration.property | Where-Object { $_.name -eq 'ContentEngineObjectStore' }).value = '%cesweep_os%'; $xml6.Save('configureContentEngineSweep.xml')"

:: Step 17: Run configureContentEngineSweep.xml
echo Running configureContentEngineSweep.xml ...
"C:\Program Files\IBM\EnterpriseRecords\configure\configmgr_cl.exe" execute -profile "C:\Program Files\IBM\EnterpriseRecords\configure\profiles\object_store_configuration_profile" -taskfile configureContentEngineSweep.xml

:: =======================
:: Completion message
echo.
echo ==========================================
echo All configuration steps are complete.
echo ==========================================
pause