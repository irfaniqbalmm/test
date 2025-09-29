@Library(['git-clone', 'clean-project']) _
def convertDbNameToSSL(dbName) {
    switch(dbName.toLowerCase()) {
        case 'db2':
            return 'DB2 SSL'
        case 'postgres':
            return 'POSTGRES SSL'
        case 'mssql':
            return 'MSSQL SSL'
        case 'oracle':
            return 'ORACLE SSL'
        case 'postgresedb':
            return 'PostgresEDB'
        default:
            error "Unsupported DB_NAME: ${dbName}"
    }
}
def convertLdapNameToSSL(ldapName) {
    switch(ldapName.toUpperCase()) {
        case 'MSAD':
            return 'MSAD SSL'
        case 'SDS':
            return 'TDS SSL'
        case 'PINGDIRECTORY':
            return 'PINGDIRECTORY SSL'
        default:
            return 'MSAD SSL'
    }
}

import groovy.json.JsonOutput
pipeline {
    agent any
    environment {
    PATH = "/usr/local/bin:$PATH"
    GITHUB_CREDS = credentials('github-credentials')
    }
    stages {
        stage('Get Cluster Data') {
            steps {
		        withCredentials([usernamePassword(credentialsId: 'github-credentials', usernameVariable: 'GITHUB_USER', passwordVariable: 'GITHUB_PASS')]) {
                    script {

                        //Properties for quickburn
                        is_multildap = 'False'
                        is_second_ldap_ssl_enabled = 'False'
                        is_quickburn = 'yes'
                        is_multildap_post_init = 'False'
                        quickburn_name = params.QUICKBURN_NAME.toLowerCase()
                        fyre_api_username = params.FYRE_API_USERNAME.toLowerCase()
                        fyre_api_key = params.FYRE_API_KEY
                        quickburn_ocp_version = params.QUICKBURN_OCP_VERSION.toLowerCase()
                        jenkins_server_password = 'Admin@123123123'
                        env.jenkins_server = 'cp4ba-jenkins1.fyre.ibm.com'

                        //General properties
                        dbname = params.DATABASE.toLowerCase()
                        ldapname = params.LDAP.toLowerCase()

                        echo "The automation will be running in a new quick burn cluster. Starting to create new quick burn cluster..."
                        echo "Cloning repository to jenkins server...."
                        sh """
                            sshpass -p '${jenkins_server_password}' ssh -o StrictHostKeyChecking=no root@${env.jenkins_server} '
                            cd /opt && \
                            echo "Creating folder: ${quickburn_name}" && \
                            rm -rf ${quickburn_name}/ && \
                            mkdir -p ${quickburn_name}/ && \
                            cd ${quickburn_name}/ && \
                            git clone -b main --depth 1 --recurse-submodules --shallow-submodules https://${GITHUB_USER}:${GITHUB_PASS}@github.ibm.com/dkrishan/Cp4ba-Automation.git && \
                            ls && \
                            cd Cp4ba-Automation/cp4ba_proddeploy_automation && \
                            echo "Inside cp4ba_proddeploy_automation" && \
                            ls && \
                            yum install -y python3.12 && \
                            python3.12 -m venv /opt/automationenv && \
                            source /opt/automationenv/bin/activate && \
                            pip3 install -r requirements.txt && \
                            pip freeze && \
                            chmod +x * && \
                            cd config && \
                            sed -i "/^\\[FYRE\\]/,/^\\[/ s/^\\s*username\\s*=.*/username = ${fyre_api_username}/" data.config && \
                            sed -i "/^\\[FYRE\\]/,/^\\[/ s/^\\s*password\\s*=.*/password = ${fyre_api_key}/" data.config && \
                            sed -i "/^\\[FYRE\\]/,/^\\[/ s/^\\s*quickburn_name\\s*=.*/quickburn_name = ${quickburn_name}/" data.config && \
                            sed -i "/^\\[FYRE\\]/,/^\\[/ s/^\\s*ocp_version\\s*=.*/ocp_version = ${quickburn_ocp_version}/" data.config && \
                            cd /opt/${quickburn_name}/Cp4ba-Automation/cp4ba_proddeploy_automation && \
                            python3 ./utils/quickburn.py && \
                            deactivate
                            '
                        """
                        sh """
                            sshpass -p '${jenkins_server_password}' scp -r -o StrictHostKeyChecking=no \
                            root@${env.jenkins_server}:/opt/${quickburn_name}/Cp4ba-Automation/cp4ba_proddeploy_automation/config/quickburn.json /tmp
                        """
                        def slurper = new groovy.json.JsonSlurper()
                        def credentialsFile = new File("/tmp/quickburn.json")
                        def jString = credentialsFile.text
                        def jData = slurper.parseText(jString)
                        KUBE_PASS = jData['kubeadmin_password']
                        echo "KUBE_PASS: ${KUBE_PASS}"
                        env.SSH_URL = "api.${quickburn_name}.cp.fyre.ibm.com"
                        ROOT_PASSWORD = params.FYRE_ACCOUNT_PASSWORD
                        cluster = quickburn_name

                        stg_prod = 'Prod'
                        if (params.STAGE_OR_PROD == 'Stage') {
                            stg_prod = 'dev'
                        }
                        
                        spd_on = 'no'
                        new_pjt_name = params.PROJECT_NAME
                        if (params.SEPARATION_DUTIES.toLowerCase() == 'yes') {
                        spd_on = 'yes'
                        new_pjt_name = new_pjt_name + 'pods'
                        }
                        currentBuild.displayName = "${cluster}-${params.BRANCH}-${params.IFixVersion}-${dbname}-${ldapname}-${params.PROJECT_NAME}"
                    }
                }
            }
        }
        stage('Set git clone parameters') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'github-credentials', usernameVariable: 'GITHUB_USER', passwordVariable: 'GITHUB_PASS')]) {
                    script {
                        echo "Going to setup the git clone and branch"
                        def envMap = getClone()
                        echo "my env maps are branchs ${envMap.branchs} and clones ${envMap.clones}"
                        git_branch=envMap.branchs
                        git_clone=envMap.clones
                        echo "Setup the git clone ${git_clone}  and branch ${git_branch}."
                    }
                }
            }
        }
        stage('Install Packages') {
            steps {
                script {
                    echo "Installing the required  python packages "
                     sh """
                        sshpass -p '${ROOT_PASSWORD}' ssh -o StrictHostKeyChecking=no root@${env.SSH_URL} '
                        oc login https://api.${cluster}.cp.fyre.ibm.com:6443 -u kubeadmin -p ${KUBE_PASS} --insecure-skip-tls-verify && \
                        echo "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@" && \
                        echo "@@ Running on \$(hostname)" && \
                        echo "@@ Cluster Name: ${cluster}" && \
                        echo "@@ Project Name: ${params.PROJECT_NAME}" && \
                        echo "@@ Proceed with Cleanup: ${params.CLEANUP}" && \
                        echo "@@ Project to clean: ${params.PROJECT_CLEAN}" && \
                        echo "@@ DB: ${dbname} " && \
                        echo "@@ LDAP: ${ldapname} " && \
                        echo "@@ Fips: ${params.FIPS.toUpperCase()} " && \
                        echo "@@ Egress: ${params.EGRESS.toUpperCase()} " && \
                        echo "@@ Separation of Duties: ${spd_on.toUpperCase()} " && \
                        echo "@@ Postgres DB for Metastore: ${params.EXTERNAL_DB_METASTORE.toUpperCase()} " && \
                        echo "@@ External Certificate: ${params.EXTERNAL_CERTIFICATE.toUpperCase()} " && \
                        echo "@@ Tablespace parameter: ${params.TABLESPACE_OPTION.toUpperCase()} " && \
                        ocpversion=\$(oc version | grep Server) && \
                        echo "@@ \${ocpversion} "  && \
                        echo "@@ Deployment type: ${params.STAGE_OR_PROD.toUpperCase()} " && \
                        echo "@@ Console link: https://console-openshift-console.apps.${cluster}.cp.fyre.ibm.com" && \
                        echo "@@ Infra node: api.${cluster}.cp.fyre.ibm.com" && \
                        echo "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@" && \
			            yum install -y python3.12 && \
                        python3.12 -m venv /opt/automationenv && \
                        source /opt/automationenv/bin/activate && \
                        echo "Installation of basic packages is done." && \
                        echo "Running on \$(hostname)" && \
                        deactivate
                        '
                    """
                    echo " Install Packages Done."
                }
            }
        }
        stage('Clone & Setup'){
            steps{
                withCredentials([usernamePassword(credentialsId: 'github-credentials', usernameVariable: 'GITHUB_USER', passwordVariable: 'GITHUB_PASS'), string(credentialsId: 'entitlement_key', variable: 'entitlement_key'), string(credentialsId: 'entitlement_prod', variable: 'entitlement_prod'), string(credentialsId: 'pull_secret_token', variable: 'pull_secret_token')]) {
                    script{
                        git_clone=git_clone
                        env.entitlement = entitlement_key
                        if (stg_prod =='Prod'){
                            env.entitlement = entitlement_prod
                        }
                        echo """Entitlement Key ${env.entitlement}"""
                        tablespace_option = params.TABLESPACE_OPTION.toUpperCase()
                        sh """
                            sshpass -p '${ROOT_PASSWORD}' ssh -o StrictHostKeyChecking=no root@${env.SSH_URL} ' \
                            cd /opt && \
                            rm -rf Cp4ba-Automation && \
                            yum install -y git  && \
                            yum install -y podman && \
                            git clone -b main --depth 1 --recurse-submodules --shallow-submodules https://${GITHUB_USER}:${GITHUB_PASS}@github.ibm.com/dkrishan/Cp4ba-Automation.git && \
                            cd /opt/Cp4ba-Automation/cp4ba_proddeploy_automation/ && \
                            source /opt/automationenv/bin/activate && \
                            pip3 install -r requirements.txt && \
                            pip freeze && \
                            chmod +x * && \
                            cd config && \
                            sed -i "s;CLONE_REPO=.*;CLONE_REPO=${git_clone};g" data.config && \
                            sed -i "s/ENTITLEMENT_KEY=.*/ENTITLEMENT_KEY=${env.entitlement}/" data.config && \
                            sed -i "s/cp_prod=.*/cp_prod=${entitlement_prod}/" data.config && \
                            sed -i "s/cp_stg=.*/cp_stg=${entitlement_key}/" data.config && \
                            sed -i "s/userandpass=.*/userandpass=${pull_secret_token}/" data.config && \
                            if [[ "NO" == ${tablespace_option} ]]
                            then
                                sed -i '' '/OS1_DB_TABLE_STORAGE_LOCATION/d' data.config && \
                                sed -i '' '/OS1_DB_INDEX_STORAGE_LOCATION/d' data.config && \
                                sed -i '' '/OS1_DB_LOB_STORAGE_LOCATION/d' data.config
                            fi

                            cd /opt/Cp4ba-Automation/cp4ba_proddeploy_automation/ && \
                            chmod +x install_java.sh && \
                            ./install_java.sh  && \
                            deactivate
                            '
                        """
                        echo """ Project clonning and setting up the configuration is done"""
                    }
                }
            }
        }
        stage('Production Deployment'){
            steps{
                script{
                    def message = "Deployment Started in ${cluster}.\nProject Name: ${params.PROJECT_NAME}\nProducts: CPE,ICN,CSS,GraphQL,CMIS,TM, BAI,IER\nDeployment type: ${params.STAGE_OR_PROD}\nFIPS: ${params.FIPS.toUpperCase()}\nEGRESS: ${params.EGRESS.toUpperCase()}\nSeparation of Duties: ${spd_on.toUpperCase()}\nPostgres DB for Metastore: ${params.EXTERNAL_DB_METASTORE.toUpperCase()}\nExternal Certificate: ${params.EXTERNAL_CERTIFICATE.toUpperCase()}\nDB: ${dbname}\nLDAP: ${ldapname}\nConsole link : https://console-openshift-console.apps.${cluster}.cp.fyre.ibm.com\nConsole Creds: kubeadmin / ${KUBE_PASS}\nInfra node: api.${cluster}.cp.fyre.ibm.com\nBuild: ${params.Build}\nIfix: ${params.IFixVersion}\nBuild_Url: ${env.BUILD_URL}"
                    env.message = message
                    def status = "success"
                    env.status = status
                    build job: 'slack-notify', parameters: [
                    string(name:'Status',value:status),
                    string(name:'MESSAGE',value:message)]
                    // slackSend (color: '#00FF00', message: "Deployment Started in  '${cluster}' (${env.BUILD_URL})")

                    def myConfig = ["db": dbname, "ldap": ldapname, "project": params.PROJECT_NAME, "branch": params.BRANCH, "stage_prod": stg_prod, "cluster_name": cluster, "cluster_pass": KUBE_PASS, "separation_duty_on": spd_on, "fips": params.FIPS, "external_db": params.EXTERNAL_DB_METASTORE, "extcrt": params.EXTERNAL_CERTIFICATE, "git_branch": git_branch, "egress": params.EGRESS, "tablespace_option": tablespace_option, "quick_burn":is_quickburn, "multildap": is_multildap, "second_ldap_ssl_enabled": is_second_ldap_ssl_enabled, "multildap_post_init": is_multildap_post_init]
                    def jsonStr = JsonOutput.toJson(myConfig)         
                    def escapedJsonStr = jsonStr.replace('"', '\\"')
                    echo "Passing JSON: ${jsonStr}"
                    echo """ ${jsonStr} """

                    sh """
                        sshpass -p '${ROOT_PASSWORD}' ssh -o StrictHostKeyChecking=no root@${env.SSH_URL} ' \
                        source /opt/automationenv/bin/activate && \
                        cd /opt/Cp4ba-Automation/cp4ba_proddeploy_automation && \
                        chmod +x ./utils/db_operations/execute_mssql_scripts/installDrivers.sh  && \
                        ./utils/db_operations/execute_mssql_scripts/installDrivers.sh  && \
                        python3 ./prod_deployment.py \"${escapedJsonStr}\" 
                        deactivate
                        '
                    """
                    echo """Project ${params.PROJECT_NAME} deploying on ${cluster}"""
                        
                }
            }
        }
        stage('Checking Deployment Status') {
            steps {
                script {
                    def bvtDbName = convertDbNameToSSL(params.DATABASE)
                    env.bvtDbName = bvtDbName
                    def bvtLdapName = convertLdapNameToSSL(params.LDAP)
                    env.bvtLdapName = bvtLdapName

                try {
                    echo " Running check_status.sh on remote server..."
                
                    def scriptOutput = sh(
                    script: """
                        sshpass -p '${ROOT_PASSWORD}' ssh -o StrictHostKeyChecking=no root@${env.SSH_URL} '
                        cd /opt &&
                        source /opt/automationenv/bin/activate &&
                        cd /opt/Cp4ba-Automation/cp4ba_proddeploy_automation/ &&
                        chmod +x check_status.sh &&
                        ./check_status.sh ${cluster} ${KUBE_PASS} ${new_pjt_name} ${params.PROJECT_NAME} &&
                        cd /opt &&
                        deactivate
                        '
                    """,
                    returnStatus: true 
                    )

                    echo "Exit Code from check_status.sh: ${scriptOutput}"

                    if (scriptOutput == 1) {
                        echo "Deployment completed successfully!"
                        def message1 = "Deployment Completed in ${cluster}.\nBuild:${params.Build}\nIfix:${params.IFixVersion}\nBuild_Url:${env.BUILD_URL}"
                        env.message1 = message1
                        def status1 = "success"
                        env.status1 = status1
                        build job: 'slack-notify', parameters: [
                        string(name: 'Status', value: status1),
                        string(name: 'MESSAGE', value: message1)
                        ]
                        echo "Starting BVT for ${cluster} (${env.BUILD_URL})"
                    } else {
                        error "Deployment failed with exit code ${scriptOutput}. Stopping pipeline."
                    }
                } catch (Exception e) {
                    echo "Error encountered: ${e.message}"
                    currentBuild.result = 'FAILURE'
                    error "Stopping pipeline due to deployment failure."
                    }
                }
            }
        }
        stage('Running BVT'){
            steps{
                build job: 'BVT_Automation', parameters: [
                string(name: 'ProjectName', value: "${new_pjt_name}"),
                string(name: 'ClusterName', value: "${cluster}"),
                string(name: 'DB', value: "${env.bvtDbName}"),
                string(name: 'LDAP', value: "${env.bvtLdapName}"),
                string(name: 'DeploymentType', value: 'production'),
                string(name: 'Build', value: "${params.Build}"),
                string(name: 'IFixVersion', value: "${params.IFixVersion}"),
                string(name: 'OC_Verify', value: "True"),
                string(name: 'QuickBurn', value: "yes"),
                string(name: 'QuickBurnName', value: "${quickburn_name}"),
                string(name: 'QuickBurnPassword', value: "${KUBE_PASS}"),
                string(name: 'QuickBurnVersion', value: "${quickburn_ocp_version}"),
                string(name: 'RootPassword', value: "${ROOT_PASSWORD}")]
            }
        }    
    }
    post {
        success {
            echo 'Deployment Pipeline success!'
        }
        failure {
            echo 'Deployment Pipeline has failed!'
        }
        always {
            sh """
                sshpass -p '${jenkins_server_password}' ssh -o StrictHostKeyChecking=no root@${env.jenkins_server} ' 
                cd /opt && \
                rm -rf ${quickburn_name}
                '
            """
        }
    }
}
