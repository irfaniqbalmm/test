from utils.utils_class import *
from db_operations import *
from utils.common import modify_configobj, svl_machine
from pull_secret import *
from utils.quickburn import *

if __name__ == "__main__":
    try:

        print(f"Number of parameters passed from prod_deployment.py file is {len(sys.argv)}")
        print(f"Parameters passed are {sys.argv[1]}")
        if len(sys.argv) < 2:
            print(len(sys.argv))
            raise Exception("Supplied arguments count is less than expected. Exiting...")

        #Getting the passed value from the dictiory
        config_dict = json.loads(sys.argv[1])
        db = config_dict.get('db', '')
        ldap = config_dict.get('ldap', '')
        project = config_dict.get('project', 'cp')
        branch = config_dict.get('branch', 'CP4BA-24.0.1-IF001')
        stage_prod = config_dict.get('stage_prod', 'dev')
        cluster_name = config_dict.get('cluster_name', 'india')
        cluster_pass = config_dict.get('cluster_pass', '')
        separation_duty_on = config_dict.get('separation_duty_on', 'no').lower()
        fips = config_dict.get('fips', 'no').lower()
        external_db = config_dict.get('external_db', 'no').lower()
        extcrt = config_dict.get('extcrt', 'no').lower()
        git_branch = config_dict.get('git_branch', 'master')
        egress = config_dict.get('egress', 'No')
        tablespace_option = config_dict.get('tablespace_option', 'yes')
        quick_burn = config_dict.get('quick_burn', 'no').lower()
        multildap = config_dict.get('multildap', 'False')
        second_ldap_ssl_enabled = config_dict.get('second_ldap_ssl_enabled', 'False')
        multildap_post_init = config_dict.get('multildap_post_init', 'False')
        component_names = config_dict.get('component_names', '')
        fisma = config_dict.get('fisma', 'NO')
        instana = config_dict.get('instana', 'NO')
        vault = config_dict.get('vault', 'NO')


        print(f'db={db} \n ldap={ldap} \n project={project} \n branch={branch} \n stage_prod={stage_prod} \n cluster_name={cluster_name} \n separation of duties={separation_duty_on} \n FIPS={fips} \n egress={egress} \n external_db={external_db} \n extcrt={extcrt} \n git_branch={git_branch} \n tablespace_option={tablespace_option} \n quick_burn={quick_burn} \n component_names={component_names}\n fisma={fisma}\n instana={instana}\n vault={vault}')
        print(f'Received parameters are {config_dict}')

        #Creating the object with the passed values
        
        deploy = Utils(config_dict)
        # Create new quick burn, create user and storage class
        if quick_burn == 'yes':
            deploy.logger.logger.info(f'Creating new dbauser.....')
            print(f'Creating new dbauser.....')
            deploy.create_user()
            deploy.logger.logger.info(f'Creating new storage class: managed-nfs-storage.....')
            print(f'Creating new storage class: managed-nfs-storage.....')
            deploy.create_storage_class()

        deploy.logger.logger.info(f'Checking that pull secrets and updating it.')
        pull_secret = deploy.check_pullsecret()
        if not pull_secret:
            deploy.logger.logger.error(f'Pull Secret updation failed.')
            raise Exception("Pull Secret updation failed.")

        # Precheck of the cluster setup. Checking ImageContentSourcePolicy
        deploy.logger.logger.info(f'Checking that ImageContentSourcePolicy/pull secrets exsists.')
        get_icsp = ['oc', 'get', 'ImageContentSourcePolicy']
        icsp_result = deploy.check_resource(get_icsp, 'mirror-config')

        # Mirror imagecontentsourcepolicy already exsits
        if icsp_result:
            try:
                # If the production ER is selected
                if stage_prod == 'Prod':
                    remove_cmd = ['oc delete ImageContentSourcePolicy mirror-config']
                    deploy.check_cluster(remove_cmd)
                    deploy.logger.logger.error(f'ICSP present for production er deployment. Removing it...')
            except Exception as e:
                deploy.logger.logger.error(f'ICSP present for production er deployment. Removing it failed.')
                raise Exception("ICSP present for production er deployment. Removeing it failed.")

        # Mirror imagecontentsourcepolicy is not available
        else:
            try:
                # If the fresh deployment is selected
                if stage_prod == 'dev':
                    create_cmd = ['oc apply -f ./config/mirror-rtp.yaml']
                    is_svl_machine = svl_machine(cluster_name)
                    if is_svl_machine:
                        create_cmd = ['oc apply -f ./config/mirror.yaml']

                    deploy.check_cluster(create_cmd)
                    deploy.logger.logger.info(f'ICSP not present for fresh production deployment. Added it automatically.')
            except Exception as e:
                deploy.logger.logger.error(f'ICSP not present for fresh production deployment and creation failed.')
                raise Exception("ICSP not present for fresh production deployment and creation failed.")
        deploy.logger.logger.info(f'Verification on ImageContentSourcePolicy success.')

        # Checking if the saplibs are up
        deploy.logger.logger.info(f'Checking the saplibs are up or not')
        saplibs_status = deploy.check_saplibs()
        if not saplibs_status:
            deploy.logger.logger.error(f'Supplied saplibs is not up and running. Please see the logs for more details.')
            exit(1)
            raise Exception("Supplied saplibs is not up and running. Please see the logs for more details.")

        # Checking the storage is created and selected
        deploy.logger.logger.info(f'Checking the cluster is having the managed-nfs-storage')
        stg_check = ['oc get storageclass -o=jsonpath="{.items[*].metadata.name}" | grep "managed-nfs-storage"']
        stg_result = deploy.check_cluster(stg_check)
        if not stg_result:
            deploy.logger.logger.error(f'Cluster is not having the storage named managed-nfs-storage. Please add the storage first.')
            raise Exception("Cluster is not having the storage named managed-nfs-storage. Please add the storage first.")

        # Prechecking of the cluster for FIPS.
        deploy.logger.logger.info(f'Deployment need to do with FIPS {fips}. Checking the cluster is fips enabled or not.')
        if fips.lower() == 'yes':
            deploy.logger.logger.info(f'Checking the cluster is fips enabled or not.')
            fips_check = ['oc get cm cluster-config-v1 -n kube-system -o jsonpath={.data.install-config} | grep "fips: true"']
            fip_result = deploy.check_cluster(fips_check)
            if not fip_result:
                deploy.logger.logger.error(f'Cluster is not FIPS enabled. Please select another cluster for FIPS enabled deployment.')
                raise Exception("Cluster is not FIPS enabled. Please select another cluster for FIPS enabled deployment.")
        
        # Setting the path in the data config file
        deploy.logger.logger.info(f'Updating the path configuration in the data config.')
        result = deploy.pathupdate_dataconfig()
        if not result:
            deploy.logger.logger.error(f'Updating the Paths in data.config file failed.')
            raise Exception("Updating the path in the data.config file is Failed.")
        
        # Clonning the cert-kubernetes
        # Initializing again as the paths are changed

        deploy = Utils(config_dict)
        deploy.logger.logger.info(f'Clonning the {branch} repository.')
        clonning = deploy.cloning_repo()
        deploy.logger.logger.info(f'Clonning status is {clonning}')
        if clonning == False:
            deploy.logger.logger.error(f'Clonning failed.')
            raise Exception("Clonning failed. Please check the logs for more details.")

        # Creating the operators by running the cluster admin script
        deploy.logger.logger.info(f'Running the cp4a admin setup.')
        run_admin = deploy.run_cp4a_clusteradmin_setup()
        if not run_admin:
            deploy.logger.logger.error(f'Running the cluster admin failed.')
            raise Exception("Running the cluster admin failed.")
        
        #check errors in pods
        deploy.logger.logger.info(f'Verify pod status')
        check_pull_secret_error()

        #Creating the property and updating it
        deploy.logger.logger.info(f'Running the property setup.')
        property_setup = deploy.property_setup()
        if not property_setup:
            deploy.logger.logger.error(f'Running the property setup and update failed.')
            raise Exception("Running the property setup and update failed.")
        
        # Validating the generated property
        validation_status = deploy.validate_generate()
        if not validation_status:
            deploy.logger.logger.error(f'Running the validation of property failed.')
            raise Exception("Running the validation of property  failed.")
            
        #Creating the secrets
        deploy.logger.logger.info(f'Creating secret.')
        secret_status = deploy.create_secret()
        if not secret_status:
            deploy.logger.logger.error(f'Create secret failed.')
            raise Exception("Create secret failed.")

        # Create sql script for im/zen/bts
        if external_db == 'yes':
            deploy.logger.logger.info(f'Creating sql statement for BTS/IM/ZEN.')
            create_sql_status = deploy.create_sql()
            if not create_sql_status:
                deploy.logger.logger.error(f'Creating sql statement for BTS/IM/ZEN failed.')
                raise Exception("Creating sql statement for BTS/IM/ZEN failed.")
            else:
                # Db deletion and creation for the external postgres to store metastore
                deploy.logger.logger.info(f'Running the Db Operations for the external postgres to store metastore.')
                DbOperations('postgres_metastore', tablespace_option)

        # Db deletion and creation
        deploy.logger.logger.info(f'Running the Db Operations.')
        DbOperations(db, tablespace_option)

        #Validation of the resources
        deploy.logger.logger.info(f'Running the validation of resources.')
        validation_status = deploy.validate_resources()
        if not validation_status:
            deploy.logger.logger.error(f'Running the validation on resources such as secret ldap, db is failed.')
            raise Exception("Running the validation on resources such as secret ldap, db is failed.")

        #Creating and Applying the CR
        if validation_status:
            deploy.logger.logger.info(f'Running the creation of the CR.')
            deployment_status = deploy.createcr_apply()
            if not deployment_status:
                deploy.logger.logger.error(f'Running the validation on custom resources is failed.')
                raise Exception("Running the validation on custom resources is failed.")

    except Exception as e:
        deploy.logger.logger.info(f'Deployment Failed with Error as : {e}')
        raise Exception(f"Deployment Failed for the Branch {branch} on namespace {project} .")
