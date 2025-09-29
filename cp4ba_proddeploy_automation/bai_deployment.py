from utils.utils_class import *
from utils.bai_utils import *
from pull_secret import *

if __name__ == "__main__":
    try:
        ldap = sys.argv[1]
        project = sys.argv[2]
        branch = sys.argv[3]
        stage_prod = sys.argv[4]
        cluster_name = sys.argv[5]
        cluster_pass = sys.argv[6]
        separation_duty_on = sys.argv[7].lower()
        metastore_db = sys.argv[8].lower()
        extcrt = sys.argv[9].lower()
        git_branch = sys.argv[10]
        egress = sys.argv[11]
        global_catalog = sys.argv[12].lower()

        print(f'ldap={ldap} \n project={project} \n branch={branch} \n stage_prod={stage_prod} \n cluster_name={cluster_name} \n separation of duties={separation_duty_on} \n Metastore db={metastore_db} \n External certificate={extcrt} \n Git branch={git_branch} \n Egress={egress} \n Global Cataloge={global_catalog}')
        bai_deploy = BaiUtils(ldap, project, branch, stage_prod, cluster_name, cluster_pass, separation_duty_on, metastore_db, extcrt, git_branch, egress, global_catalog)
        
        config_dict = {
            'db': None, 'ldap':ldap, 'project':project, 'branch':branch, 'stage_prod':stage_prod,
            'cluster_name':cluster_name, 'cluster_pass':cluster_pass, 'separation_duty_on':separation_duty_on, 'fips': 'no',
            'metastore_db': metastore_db, 'extcrt':extcrt, 'git_branch': git_branch, 'egress':egress, 'global_catalog': global_catalog
        }
        cp_deploy = Utils(config_dict)

        #Verying pull secrets are updated
        bai_deploy.logger.logger.info('Checking and updating pull secrets...')
        print('Checking and updating pull secrets...')
        pull_secret = cp_deploy.check_pullsecret()
        if not pull_secret:
            bai_deploy.logger.logger.error(f'Pull Secret updation failed.')
            raise Exception("Pull Secret updation failed.")
        
        # Precheck of the cluster setup. Checking ImageContentSourcePolicy
        bai_deploy.logger.logger.info('Checking that ImageContentSourcePolicy/pull secrets exsists.')
        print('Checking that ImageContentSourcePolicy/pull secrets exsists.')
        get_icsp = ['oc', 'get', 'ImageContentSourcePolicy']
        icsp_result = cp_deploy.check_resource(get_icsp, 'mirror-config')

        # Mirror imagecontentsourcepolicy already exsits
        if icsp_result:
            try:
                # If the production ER is selected
                if stage_prod == 'Prod':
                    remove_cmd = ['oc delete ImageContentSourcePolicy mirror-config']
                    cp_deploy.check_cluster(remove_cmd)
                    bai_deploy.logger.logger.error('ICSP present for production er deployment. Removing it...')
                    print('ICSP present for production er deployment. Removing it...')
            except Exception as e:
                bai_deploy.logger.logger.error(f'ICSP present for production er deployment. Removing failed.')
                raise Exception("ICSP present for production er deployment. Removing failed.")

        # Mirror imagecontentsourcepolicy is not available
        else:
            try:
                # If the fresh deployment is selected
                if stage_prod == 'dev':
                    is_svl_machine = svl_machine(cluster_name)
                    if is_svl_machine:
                        create_cmd = ['oc apply -f ./config/mirror.yaml']
                    else:
                        create_cmd = ['oc apply -f ./config/mirror-rtp.yaml']
                    
                    cp_deploy.check_cluster(create_cmd)
                    bai_deploy.logger.logger.info('ICSP not present for fresh production deployment. Added it automatically.')
                    print('ICSP not present for fresh production deployment. Added it automatically.')
            except Exception as e:
                bai_deploy.logger.logger.error(f'ICSP not present for fresh production deployment and creation failed.')
                raise Exception("ICSP not present for fresh production deployment and creation failed.")
        bai_deploy.logger.logger.info('Successfuly verified ImageContentSourcePolicy.')
        print('Successfuly verified ImageContentSourcePolicy.')

        # Setting the path in the data config file
        bai_deploy.logger.logger.info(f'Updating the path configuration in the data config.')
        result = bai_deploy.bai_pathupdate_dataconfig()
        if not result:
            bai_deploy.logger.logger.error(f'Updating the Paths in data.config file failed.')
            raise Exception("Updating the path in the data.config file is Failed.")
        
        # Initializing again as the paths are changed
        bai_deploy = BaiUtils(ldap, project, branch, stage_prod, cluster_name, cluster_pass, separation_duty_on, metastore_db, extcrt, git_branch, egress, global_catalog)
        bai_deploy.logger.logger.info(f'Clonning the {branch} repository.')
        print(f'Clonning the {branch} repository.')
        is_clone = bai_deploy.cloning_repo()
        bai_deploy.logger.logger.info(f'Clonning status is {is_clone}')
        print(f'Clonning status is {is_clone}')
        if is_clone == False:
            bai_deploy.logger.logger.error(f'Clonning failed.')
            raise Exception("Clonning failed. Please check the logs for more details.")
            
        # Installing the operators by running the cluster admin script
        bai_deploy.logger.logger.info('Running bai cluster admin setup.')
        print('Running bai cluster admin setup.')
        run_admin = bai_deploy.run_bai_clusteradmin_setup()
        if not run_admin:
            bai_deploy.logger.logger.error(f'Running the cluster admin failed.')
            raise Exception("Running the cluster admin failed.")
        
        # check errors in pods
        bai_deploy.logger.logger.info('Verifying pod status...')
        print('Verifying pod status...')
        check_pull_secret_error()

        # Creating the property and updating it
        bai_deploy.logger.logger.info('Running bai-prerequisite.sh -m property and updating the property files...')
        print('Running bai-prerequisite.sh -m property and updating the property files...')
        property_setup = bai_deploy.run_bai_property()
        if not property_setup:
            bai_deploy.logger.logger.error(f'Running bai-prerequisite.sh -m property failed.')
            raise Exception("Running bai-prerequisite.sh -m property failed.")
        update_property = bai_deploy.update_property_files()
        if not update_property:
            bai_deploy.logger.logger.error(f'Failed to update the property files')
            raise Exception("Failed to update the property files")
        
        # Validating the generated property
        validation_status = bai_deploy.validate_generate()
        if not validation_status:
            bai_deploy.logger.logger.error(f'Running the validation of property failed. Property files are not generated/updated properly.')
            raise Exception("Running the validation of property failed.Property files are not generated/updated properly.")
        
        # Running prerequisite generate and creating the secrets
        bai_deploy.logger.logger.info(f'Running bai-prerequisites.sh -m generate...')
        print(f'Running bai-prerequisites.sh -m generate...')
        generate_script = bai_deploy.run_bai_generate()
        if not generate_script:
            bai_deploy.logger.logger.error(f'Running bai-prerequisites.sh -m generate failed.')
            raise Exception("Running bai-prerequisites.sh -m generate failed.")
        
        bai_deploy.logger.logger.info(f'Creating secret...')
        print(f'Creating secret...')
        secret_status = bai_deploy.create_secret()
        if not secret_status:
            bai_deploy.logger.logger.error(f'Create secret failed.')
            raise Exception("Create secret failed.")
        
        # Validation of the resources
        bai_deploy.logger.logger.info('Running prerequisite validate...')
        print('Running prerequisite validate...')
        validation_status = bai_deploy.bai_validation()
        if not validation_status:
            bai_deploy.logger.logger.error('BAI validation failed.')
            raise Exception('BAI validation failed.')
        
        # Run bai-deployment.sh and generate the CR file
        bai_deploy.logger.logger.info('Running bai-deployment.sh and generating CR file...')
        print('Running bai-deployment.sh and generating CR file...')
        cr = bai_deploy.run_bai_deployment()
        if not cr:
            bai_deploy.logger.logger.error('Running bai-deployment.sh and generating CR file failed.')
            raise Exception('Running bai-deployment.sh and generating CR file failed.')
        
        # Apply the CR file and verify
        bai_deploy.logger.logger.info('Applying the generated CR file...')
        print('Applying the generated CR file...')
        apply_cr = bai_deploy.apply_bai_cr()
        if not apply_cr:
            bai_deploy.logger.logger.error('Failed to apply the generated bai cr')
            raise Exception('Failed to apply the generated bai cr')
        validate_cr = bai_deploy.validate_deployment()
        if not validate_cr:
            bai_deploy.logger.logger.error('The bai CR is not present in the cluster')
            raise Exception('The bai CR is not present in the cluster')

    except Exception as e:
        bai_deploy.logger.logger.info(f'Deployment Failed with Error as : {e}')
        raise Exception(f"Deployment Failed for the Branch {branch} on namespace {project} .")