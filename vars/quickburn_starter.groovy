def modifyBranch(branch) {
    switch(branch) {
        case "2401":
            return "CP4BA-24.0.1"
        case "24.0.0-IF003":
            return "CP4BA-24.0.0-IF003"
        case "24.0.0-IF004":
            return "24.0.0"
        case "24.0.0-IF002":
            return "CP4BA-24.0.0-IF002"
        case "24.0.0":
            return "CP4BA-24.0.0"
        case "24.0.0-IF005":
            return "24.0.0"
        case "24.0.0-IF001":
            return "CP4BA-24.0.0-IF001"
        case "24.0.1-IF001":
            return "24.0.1"
        case "25.0.0":
            return "master"
        default:
            return branch // If no match, return the original branch
    }
}

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
                        is_quickburn = 'yes'
                        quickburn_name = params.QUICKBURN_NAME.toLowerCase()
                        fyre_api_username = params.FYRE_API_USERNAME.toLowerCase()
                        fyre_api_key = params.FYRE_API_KEY
                        quickburn_ocp_version = params.QUICKBURN_OCP_VERSION.toLowerCase()
                        jenkins_server_password = 'Admin@123123123'
                        env.jenkins_server = 'cp4ba-jenkins1.fyre.ibm.com'
                        
                        echo "The starter deployment automation will be running in a new quick burn cluster. Starting to create new quick burn cluster..."
                        echo "Cloning repository to jenkins server...."
                        sh """
                            sshpass -p '${jenkins_server_password}' ssh -o StrictHostKeyChecking=no root@${env.jenkins_server} '
                            cd /opt && \
                            echo "Creating folder: ${quickburn_name}" && \
                            rm -rf ${quickburn_name}/ && \
                            mkdir -p ${quickburn_name}/ && \
                            cd ${quickburn_name}/ && \
                            git clone --depth 1 --recurse-submodules --shallow-submodules https://${GITHUB_USER}:${GITHUB_PASS}@github.ibm.com/dkrishan/Cp4ba-Automation.git && \
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

                        //Copying the created quickburn.json file to tmp
                        sh """
                            mkdir -p /tmp/${quickburn_name}/ && \
                            sshpass -p Admin@123123123 scp -r -o StrictHostKeyChecking=no \
                            root@${env.jenkins_server}:/opt/${quickburn_name}/Cp4ba-Automation/cp4ba_proddeploy_automation/config/quickburn.json /tmp/${quickburn_name}
                        """

                        //Reading the values from the quickburn.json
                        def slurper = new groovy.json.JsonSlurper()
                        def credentialsFile = new File("/tmp/${quickburn_name}/quickburn.json")
                        def jString = credentialsFile.text
                        def jData = slurper.parseText(jString)
                        KUBE_PASS = jData['kubeadmin_password']
                        echo "KUBE_PASS: ${KUBE_PASS}"
                        env.SSH_URL = "api.${quickburn_name}.cp.fyre.ibm.com"
                        ROOT_PASSWORD = params.FYRE_ACCOUNT_PASSWORD
                        cluster = quickburn_name
                        git_branch=params.BRANCH
                        git_clone = "https://${GITHUB_USER}:${GITHUB_PASS}@github.com/icp4a/cert-kubernetes.git"

                        if (params.BRANCH == '25.0.0') {
                            git_branch='master'
                            git_clone = "https://${GITHUB_USER}:${GITHUB_PASS}@github.ibm.com/dba/cert-kubernetes.git"
                        }

                        if (params.BRANCH == '24.0.0-IF005') {
                            git_branch='24.0.0'
                            git_clone = "https://${GITHUB_USER}:${GITHUB_PASS}@github.ibm.com/dba/cert-kubernetes.git"
                        }

                        if (params.BRANCH == '24.0.1-IF002') {
                            git_branch='24.0.1'
                            git_clone = "https://${GITHUB_USER}:${GITHUB_PASS}@github.ibm.com/dba/cert-kubernetes.git"
                        }

                        def git_clone = "git clone -b ${git_branch} --depth 1 --recurse-submodules --shallow-submodules ${git_clone}"
                        env.git_clone = git_clone
                        env.cluster = cluster
                        echo "${cluster}"
                        env.SSH_PASSWORD = ROOT_PASSWORD
                        env.SSH_USER = "root"
                        env.SSH_URL = "api.${cluster}.cp.fyre.ibm.com"
                        env.KUBE_PASS = KUBE_PASS
                        echo "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"
                        echo "@@ Running on ${env.SSH_URL}"
                        echo "@@ Cluster Name: ${env.cluster}"
                        echo "@@ Project Name: ${params.Project}"
                        echo "@@ Deployment type: Starter"
                        echo "@@ Branch Name: ${params.BRANCH}"
                        echo "@@ IFix ${params.IFixVersion}"
                        echo "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"
                        env.jsonData = jData
                        currentBuild.displayName = "${cluster}-${params.BRANCH}-${params.IFixVersion}-Starter-${params.Project}"
                    }
                }
            }
        }
        stage('Starter Deployment'){
            steps{
                withCredentials([usernamePassword(credentialsId: 'github-credentials', usernameVariable: 'GITHUB_USER', passwordVariable: 'GITHUB_PASS'), string(credentialsId: 'entitlement_key', variable: 'entitlement_key'), string(credentialsId: 'entitlement_prod', variable: 'entitlement_prod'), string(credentialsId: 'pull_secret_token', variable: 'pull_secret_token')]) {
                script{
                    // slackSend (color: '#00FF00', message: "Deployment Started in  '${params.CLUSTER_NAME}' (${env.BUILD_URL})")
                    env.entitlement = entitlement_key
                    def Ifix = params.IFixVersion
                    env.Ifixr = Ifix.replace(' ','')
                    sh """
                        sshpass -p '${env.SSH_PASSWORD}' ssh -o StrictHostKeyChecking=no ${env.SSH_USER}@${env.SSH_URL} '
                        cd /opt && \
                        yum install -y python3.12 && \
                        rm -rf Cp4ba-Automation/ && \
                        rm -rf Starter_automation/ && \
                        rm -rf automation/ && \
                        yum install -y git  && \
                        yum install -y podman && \
                        git clone --depth 1 --recurse-submodules --shallow-submodules https://${GITHUB_USER}:${GITHUB_PASS}@github.ibm.com/dkrishan/Cp4ba-Automation.git && \
                        cd /opt/Cp4ba-Automation/Starter-Deployment/Starter_automation/ && \
                        chmod -R +x * && \
                        python3.12 -m venv venv && \
                        source venv/bin/activate && \
                        cd config_files && \
                        sed -i "/\\[ocp_details\\]/,/^\\[/ s/USERNAME = .*/USERNAME = kubeadmin/" data.config && \
                        sed -i "/\\[ocp_details\\]/,/^\\[/ s/PASSWORD = .*/PASSWORD = ${env.KUBE_PASS}/" data.config && \
                        sed -i "/\\[ocp_details\\]/,/^\\[/ s/CLUSTER_IP = .*/CLUSTER_IP = ${env.SSH_URL}/" data.config && \
                        sed -i "/\\[project_name\\]/,/^\\[/ s/NAMESPACE = .*/NAMESPACE = ${params.Project}/" data.config && \
                        sed -i "/\\[cluster_admin_setup\\]/,/^\\[/ s/ENTITLEMENT_KEY = .*/ENTITLEMENT_KEY = ${env.entitlement}/" data.config && \
                        sed -i "/\\[git_command_details\\]/,/^\\[/ s|GIT_CLONE_COMMAND = .*|GIT_CLONE_COMMAND = '${env.git_clone}'|" data.config &&\
                        sed -i "/\\[deployment_options\\]/,/^\\[/ s/Build = .*/Build = ${params.Build}/" data.config && \
                        sed -i "/\\[deployment_options\\]/,/^\\[/ s/IFixVersion = .*/IFixVersion = ${Ifixr}/" data.config && \
                        sed -i "s/cp_prod=.*/cp_prod=${entitlement_prod}/" data.config && \
                        sed -i "s/cp_stg=.*/cp_stg=${entitlement_key}/" data.config && \
                        sed -i "s/userandpass=.*/userandpass=${pull_secret_token}/" data.config && \
                        cd .. && \
                        pip3 install -r requirements.txt && \
                        ./starter_automation.sh && \
                        deactivate
                        '
                    """
                    }
                }
            }
        }
        stage('Checking Deployment status'){
            steps{
                script{
                    sh """
                        sshpass -p '${env.SSH_PASSWORD}' ssh -o StrictHostKeyChecking=no ${env.SSH_USER}@${env.SSH_URL} ' \
                        cd /opt/Cp4ba-Automation/Starter-Deployment/Starter_automation/ && \
                        source venv/bin/activate && \
                        cd /opt/Cp4ba-Automation/cp4ba_proddeploy_automation/ && \
                        chmod +x * && \
                        ./check_status.sh ${cluster} ${env.KUBE_PASS} ${params.Project} ${params.PROJECT_NAME} && \
                        cd /opt
                        deactivate
                        '
                    """
                    echo """ Starting BVT for ${cluster}"""
                }
            }
        }
        stage('Bvt Runs'){
            steps{
                build job: 'BVT_Automation', parameters: [
                string(name: 'ProjectName', value: "${params.Project}"),
                string(name: 'ClusterName', value: "${params.CLUSTER_NAME}"),
                string(name: 'DB', value: 'POSTGRES SQL'),
                string(name: 'LDAP', value: 'Open LDAP'),
                string(name: 'DeploymentType', value: 'starter'),
                string(name: 'Build', value: "${params.Build}"),
                string(name: 'IFixVersion', value: "${params.IFixVersion}"),
                string(name: 'Bvt_User', value: "admin"),
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
            echo 'Deployment completed successfully!'
        }
        failure {
            echo 'Pipeline has failed!'
        }
        always {
            sh """
                sshpass -p '${jenkins_server_password}' ssh -o StrictHostKeyChecking=no root@${env.jenkins_server} ' 
                cd /opt && \
                rm -rf ${quickburn_name}
                '
            """
            //Removing the folder created
            sh """
                rm -rf /tmp/${quickburn_name}
            """
        }
    }
}
