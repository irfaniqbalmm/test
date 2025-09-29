@Library(['git-clone', 'clean-project']) _
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
                        sh('curl -u ${GITHUB_USER}:${GITHUB_PASS} -o /tmp/clusters_data.json https://raw.github.ibm.com/Cp4ba-auto/Cp4ba-Automation/main/CP4BA_Package/clusters.json')
                        def jsonSlurper = new groovy.json.JsonSlurper()
                        def inputFile = new File("/tmp/clusters_data.json")
                        def jsonString = inputFile.text
                        def jsonData = jsonSlurper.parseText(jsonString)
                        def cluster = params.CLUSTER_NAME.toLowerCase()
                        env.cluster = cluster
                        echo "${cluster}"
                        ROOT_PASSWORD = jsonData[cluster].root_pwd
                        env.SSH_USER = "root"
                        env.SSH_URL = "api.${cluster}.cp.fyre.ibm.com"
                        KUBE_PASS = jsonData[cluster].kube_pwd
                        echo "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"
                        echo "@@ Running on \$(hostname)"
                        echo "@@ Cluster Name: ${params.CLUSTER_NAME}"
                        echo "@@ Project Name: ${params.Project}"
                        echo "@@ Deployment type: Starter"
                        echo "@@ Branch Name: ${params.BRANCH}"
                        echo "@@ IFix ${params.IFixVersion}"
                        echo "@@ Cleanup project: ${params.CLEANUP}"
                        echo "@@ Project to cleanup: ${params.PROJECT_CLEAN}"
                        echo "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"
                        env.jsonData = jsonData
                        currentBuild.displayName = "${cluster}-${params.BRANCH}-${params.IFixVersion}-Starter-${params.Project}"
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
        stage('Clean Project') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'github-credentials', usernameVariable: 'GITHUB_USER', passwordVariable: 'GITHUB_PASS')]) {
                    script {
                        cleanProject(cluster, ROOT_PASSWORD, KUBE_PASS, git_branch, git_clone)
                    }
                }
            }
        }
        stage('Starter Deployment'){
            steps{
                withCredentials([usernamePassword(credentialsId: 'github-credentials', usernameVariable: 'GITHUB_USER', passwordVariable: 'GITHUB_PASS'), string(credentialsId: 'entitlement_key', variable: 'entitlement_key'), string(credentialsId: 'entitlement_prod', variable: 'entitlement_prod'), string(credentialsId: 'pull_secret_token', variable: 'pull_secret_token')]) {
                script{
                    // slackSend (color: '#00FF00', message: "Deployment Started in  '${params.CLUSTER_NAME}' (${env.BUILD_URL})")
                    env.git_clone = "git clone -b ${git_branch} --depth 1 --recurse-submodules --shallow-submodules https:\\/\\/${GITHUB_USER}:${GITHUB_PASS}@github.ibm.com\\/dba\\/cert-kubernetes.git"
                     
                    echo "Going to clone from the repo ${git_clone}"
                    env.entitlement = entitlement_key
                    def Ifix = params.IFixVersion
                    env.Ifixr = Ifix.replace(' ','')
                    sh """
                        sshpass -p '${ROOT_PASSWORD}' ssh -o StrictHostKeyChecking=no ${env.SSH_USER}@${env.SSH_URL} '
                        
                        echo "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@" && \
                        echo "KUBE_PASS ${KUBE_PASS}" && \
                        echo "SSH_URL: ${env.SSH_URL}}" && \
                        echo "Project Name to clean : ${params.Project}" && \
                        echo "entitlement ${env.entitlement} " && \
                        echo "git_clone ${env.git_clone} " && \
                        echo "entitlement ${params.Build} " && \
                        echo "Ifixr ${Ifixr} " && \
                        echo "pull_secret_token ${pull_secret_token} " && \
                        echo "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@" && \
                        
                        cd /opt && \
                        yum install -y python3.12 && \
                        rm -rf Cp4ba-Automation/ && \
                        rm -rf Starter_automation/ && \
                        rm -rf automation/ && \
                        git clone -b main --depth 1 --recurse-submodules --shallow-submodules https://${GITHUB_USER}:${GITHUB_PASS}@github.ibm.com/dkrishan/Cp4ba-Automation.git && \
                        cd /opt/Cp4ba-Automation/Starter-Deployment/Starter_automation/ && \
                        chmod -R +x * && \
                        python3.12 -m venv venv && \
                        cd config_files && \
                        sed -i "/\\[ocp_details\\]/,/^\\[/ s/USERNAME = .*/USERNAME = kubeadmin/" data.config && \
                        sed -i "/\\[ocp_details\\]/,/^\\[/ s/PASSWORD = .*/PASSWORD = ${KUBE_PASS}/" data.config && \
                        sed -i "/\\[ocp_details\\]/,/^\\[/ s/CLUSTER_IP = .*/CLUSTER_IP = ${env.SSH_URL}/" data.config && \
                        sed -i "/\\[project_name\\]/,/^\\[/ s/NAMESPACE = .*/NAMESPACE = ${params.Project}/" data.config && \
                        sed -i "/\\[cluster_admin_setup\\]/,/^\\[/ s/ENTITLEMENT_KEY = .*/ENTITLEMENT_KEY = ${env.entitlement}/" data.config && \
                        sed -i "/\\[deployment_options\\]/,/^\\[/ s/Build = .*/Build = ${params.Build}/" data.config && \
                        sed -i "/\\[deployment_options\\]/,/^\\[/ s/IFixVersion = .*/IFixVersion = ${Ifixr}/" data.config && \
                        sed -i "s/cp_prod=.*/cp_prod=${entitlement_prod}/" data.config && \
                        sed -i "s/cp_stg=.*/cp_stg=${entitlement_key}/" data.config && \
                        sed -i "s/userandpass=.*/userandpass=${pull_secret_token}/" data.config && \
                        sed -i "/\\[git_command_details\\]/,/^\\[/ s/GIT_CLONE_COMMAND = .*/GIT_CLONE_COMMAND = ${env.git_clone}/" data.config && \
                        cd .. && \
                        sed -i "1d" requirements.txt && \
                        source venv/bin/activate && \
                        pip install -r requirements.txt && \
                        sed -i "s|/usr/bin/python3.9|/opt/Cp4ba-Automation/Starter-Deployment/Starter_automation/venv/bin/python|g" starter_automation.sh && \
                        deactivate && \
                        ./starter_automation.sh && \
                        cd /opt/Cp4ba-Automation/cp4ba_proddeploy_automation &&\
                        ./check_status.sh ${params.CLUSTER_NAME} ${KUBE_PASS} ${params.Project} ${params.Project} &&\
                        cd /opt
                        '
                    """
                    // slackSend (color: '#00FF00', message: "Deployment Succeeded in  '${params.CLUSTER_NAME}' (${env.BUILD_URL})")
                    }
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
                string(name: 'QuickBurn', value: "No")]
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
    }
}
