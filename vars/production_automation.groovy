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
                        // URL to the JSON file
                        sh('curl -u ${GITHUB_USER}:${GITHUB_PASS} -o /tmp/clusters_data.json https://raw.github.ibm.com/dkrishan/Cp4ba-Automation/main/CP4BA_Package/clusters.json')

                        // Parse the JSON content
                        def jsonSlurper = new groovy.json.JsonSlurper()
                        def inputFile = new File("/tmp/clusters_data.json")
                        def jsonString = inputFile.text
                        def jsonData = jsonSlurper.parseText(jsonString)
                        
                        dbname = params.DATABASE.toLowerCase()
                        ldapname = params.LDAP.toLowerCase()
                        cluster = params.CLUSTER_NAME.toLowerCase()
                        ROOT_PASSWORD = jsonData[cluster].root_pwd
                        KUBE_PASS = jsonData[cluster].kube_pwd
                        env.SSH_URL = "api.${cluster}.cp.fyre.ibm.com"

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
        stage('Clean Project') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'github-credentials', usernameVariable: 'GITHUB_USER', passwordVariable: 'GITHUB_PASS')]) {
                    script {
                        cleanProject(cluster, ROOT_PASSWORD, KUBE_PASS, git_branch, git_clone)
                    }
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
                        sh """
                            sshpass -p '${ROOT_PASSWORD}' ssh -o StrictHostKeyChecking=no root@${env.SSH_URL} ' \
                            cd /opt && \
                            rm -rf Cp4ba-Automation && \
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
                            sed -i '' '/OS1_DB_TABLE_STORAGE_LOCATION/d' data.config && \
                            sed -i '' '/OS1_DB_INDEX_STORAGE_LOCATION/d' data.config && \
                            sed -i '' '/OS1_DB_LOB_STORAGE_LOCATION/d' data.config
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
                    is_quickburn = 'no'
                    multildap = 'False'
                    second_ldap_ssl_enabled = 'False'
                    multildap_post_init = 'False'
                    external_db_metastore = 'no'
                    external_certificate = 'no'
                    tablespace_option = 'no'
		            component_names = 'content search services,content management interoperability services,ibm enterprise records,ibm content collector for sap,business automation insights,task manager'
                    def message = "Deployment Started in ${cluster}.\nProject Name: ${params.PROJECT_NAME}\nProducts: CPE,ICN,CSS,GraphQL,CMIS,TM, BAI,IER\nDeployment type: ${params.STAGE_OR_PROD}\nFIPS: ${params.FIPS.toUpperCase()}\nEGRESS: ${params.EGRESS.toUpperCase()}\nSeparation of Duties: ${spd_on.toUpperCase()}\nPostgres DB for Metastore: ${external_db_metastore.toUpperCase()}\nExternal Certificate: ${external_certificate.toUpperCase()}\nDB: ${dbname}\nLDAP: ${ldapname}\nConsole link : https://console-openshift-console.apps.${cluster}.cp.fyre.ibm.com\nConsole Creds: kubeadmin / ${KUBE_PASS}\nInfra node: api.${cluster}.cp.fyre.ibm.com\nBuild: ${params.Build}\nIfix: ${params.IFixVersion}\nBuild_Url: ${env.BUILD_URL}"
                    env.message = message
                    def status = "success"
                    env.status = status
                    build job: 'slack-notify', parameters: [
                    string(name:'Status',value:status),
                    string(name:'MESSAGE',value:message)]
                    // slackSend (color: '#00FF00', message: "Deployment Started in  '${cluster}' (${env.BUILD_URL})")
                    echo """Parameters being passed to prod_deployment.sh:
                        DB Name: ${dbname}
                        LDAP Name: ${ldapname}
                        Project Name: ${params.PROJECT_NAME}
                        Branch: ${params.BRANCH}
                        Stage/Prod: ${stg_prod}
                        Cluster: ${cluster}
                        Kube Pass: ${KUBE_PASS}
                        Separation of Duties: ${spd_on}
                        FIPS: ${params.FIPS}
                        External DB Metastore: ${external_db_metastore}
                        External Certificate: ${external_certificate}
                        Git Branch: ${git_branch}
                        Egress: ${params.EGRESS}
                        Tablespace Option: ${tablespace_option}
                        Quick Burn: ${is_quickburn}
                        Multi LDAP: ${multildap}
                        Second LDAP SSL Enabled: ${second_ldap_ssl_enabled}
                        Multi LDAP Post Init: ${multildap_post_init}
                    """

                    def myConfig = ["db": dbname, "ldap": ldapname, "project": params.PROJECT_NAME, "branch": params.BRANCH, "stage_prod": stg_prod, "cluster_name": cluster, "cluster_pass": KUBE_PASS, "separation_duty_on": spd_on, "fips": params.FIPS, "external_db": external_db_metastore, "extcrt": external_certificate,"git_branch": git_branch, "egress": params.EGRESS, "tablespace_option": tablespace_option, "quick_burn":is_quickburn, "multildap": multildap, "second_ldap_ssl_enabled": second_ldap_ssl_enabled, "multildap_post_init": multildap_post_init, "component_names":component_names]
                    def jsonStr = JsonOutput.toJson(myConfig)         
                    def escapedJsonStr = jsonStr.replace('"', '\\"')
                    echo "Passing JSON: ${jsonStr}"
                    echo """ ${jsonStr} """


                    def scriptstatus = sh(script: """
                        sshpass -p '${ROOT_PASSWORD}' ssh -o StrictHostKeyChecking=no root@${env.SSH_URL} ' \
			set -e && \
                        source /opt/automationenv/bin/activate && \
                        cd /opt/Cp4ba-Automation/cp4ba_proddeploy_automation && \
                        chmod +x ./utils/db_operations/execute_mssql_scripts/installDrivers.sh  && \
                        ./utils/db_operations/execute_mssql_scripts/installDrivers.sh  && \
			echo "Setup completed" && \
                        python3 ./prod_deployment.py \"${escapedJsonStr}\"
                        deactivate
                        '
                    """, returnStatus: true)

                    // Print the result to the Jenkins log
                    echo "Python script output: ${scriptstatus}"

                    
                    if (scriptstatus != 0) {
                        error "Python script failed with exit code ${status}"
                    }
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
        stage('Add Network policy') {
            when {
                expression {
                    def str = params.BRANCH
                    def sub = str.substring(0, 6)
                    return params.EGRESS.toUpperCase() == 'YES' && sub == '25.0.0'
                }
            }
            steps {
                withCredentials([usernamePassword(credentialsId: 'github-credentials', usernameVariable: 'GITHUB_USER', passwordVariable: 'GITHUB_PASS')]) {
                    script {
                        sh """
                            sshpass -p '${ROOT_PASSWORD}' ssh -o StrictHostKeyChecking=no root@${env.SSH_URL} ' \
                            cd /opt && \
                            source /opt/automationenv/bin/activate && \
                            cd /opt/Cp4ba-Automation/cp4ba_proddeploy_automation/ && \
                            chmod +x * && \
			    python3 network_policy.py ${params.PROJECT_NAME} && \
                            cd /opt
                            deactivate
                            '
                        """
                        echo "Additional LDAP details added."
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
                string(name: 'QuickBurn', value: "No"),
                string(name: 'Multildap', value: "False")]
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
    }
}
