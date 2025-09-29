def get_user(Bvt_User) {
    switch(Bvt_User) {
        case 'admin':
            return 'admin'
        case 'non-admin':
            return 'non-admin'
        case 'both':
            return 'both'
        
        default:
            error "Unsupported LDAP_NAME: ${ldapName}"
    }
}

def findFirstAvailableNode(agents) {
    for (agent in agents) {
        def node = Jenkins.instance.getNode(agent)
        echo "The node istance is ${node}"
        if (node != null) {
            echo "${node} is not null"
            def computer = node.toComputer()
            if (computer != null && computer.isOnline() && computer.isIdle()) {
                echo "Agent ${agent} is online and idle."
                return agent
            } else {
                echo "Agent ${agent} is not available (online: ${computer?.isOnline()}, idle: ${computer?.isIdle()})."
            }
        } else {
            echo "Agent ${agent} does not exist."
        }
    }
    return null
}

@NonCPS
def extractFirstMatch(String text, String pattern, String defaultValue = "Not found") {
    def matcher = (text =~ pattern)
    return matcher.find() ? matcher[0][1] : defaultValue
}

pipeline {
    agent none
    environment {
        bvtreport = 'BVT_CP4BA'
        mvtreport = 'MVT_CP4BA'
    }
    stages {
        stage('Check Agents and Run Build') {
            steps {
                script {
                    def agents = ['bvt1', 'bvtauto1']
                    def selectedAgent = null

                    timeout(time: 60, unit: 'MINUTES') {
                        waitUntil {
                            selectedAgent = findFirstAvailableNode(agents)
                            return selectedAgent != null
                        }
                    }

                    if (selectedAgent == null) {
                        error("No agent available within the timeout period")
                    }
                    echo "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"
                    echo "Selected agent: ${selectedAgent}"
                    echo "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"
                    currentBuild.displayName = "${params.ClusterName}-${params.ProjectName}-${selectedAgent}-${params.DB}-${params.LDAP}-${params.Build}-${params.IFixVersion}"
                    node(selectedAgent) {
                        
                        if (params.QuickBurn == "yes") {
                            cluster = params.QuickBurnName.toLowerCase()
                            echo "BVT running for a deployment in quick burn cluster ${cluster}..."
                            env.KUBE_PASS = params.QuickBurnPassword
                            env.ocp = params.QuickBurnVersion
                            env.ROOT_PASSWORD = params.RootPassword
                            env.SSH_URL = "api.${cluster}.cp.fyre.ibm.com"
                        } else {
                            cluster = params.ClusterName
                        }

                        echo "Running build on agent: ${selectedAgent}"
                        
                        echo "Getting Latest BVT Code..."
                        bat '''
                            cd C:\\CP4BA_BVT_Automation
                            python "git_pull&open.py"
                        '''
                        
                        // Define PowerShell script content
                        def powershellScript = """
                            \$configFile = 'C:\\CP4BA_BVT_Automation\\Cp4ba-Automation\\CP4BA_Package\\config.ini'
                            
                            # Replace 'build' line in config.ini
                            (Get-Content \$configFile) |
                            ForEach-Object { \$_ -replace 'build\\s*=.*', 'build = ${params.Build}' } |
                            Set-Content \$configFile
                            echo "Build : ${params.Build}"
                            
                            (Get-Content \$configFile) |
                            ForEach-Object { \$_ -replace 'ifix_version\\s*=.*', 'ifix_version = ${params.IFixVersion}'} |
                            Set-Content \$configFile
                            echo "IFix : ${params.IFixVersion}"
                            
                            (Get-Content \$configFile) |
                            ForEach-Object { \$_ -replace 'project_name\\s*=.*', 'project_name = ${params.ProjectName}' } |
                            Set-Content \$configFile
                            echo "Namespace : ${params.ProjectName}"
                            
                            (Get-Content \$configFile) |
                            ForEach-Object { \$_ -replace 'cluster\\s*=.*', 'cluster = ${params.ClusterName.toLowerCase()}' } |
                            Set-Content \$configFile
                            echo "Cluster : ${params.ClusterName.toLowerCase()}"
                            
                            (Get-Content \$configFile) |
                            ForEach-Object { \$_ -replace 'db\\s*=.*', 'db = ${params.DB}' } |
                            Set-Content \$configFile
                            echo "Database : ${params.DB}"
                            
                            (Get-Content \$configFile) |
                            ForEach-Object { \$_ -replace 'ldap\\s*=.*', 'ldap = ${params.LDAP}' } |
                            Set-Content \$configFile
                            echo "LDAP : ${params.LDAP}"
                            
                            (Get-Content \$configFile) |
                            ForEach-Object { \$_ -replace 'deployment_type\\s*=.*', 'deployment_type = ${params.DeploymentType}' } |
                            Set-Content \$configFile
                            echo "Deployment type : ${params.DeploymentType}"
                            
                            (Get-Content \$configFile) |
                            ForEach-Object { \$_ -replace 'user\\s*=.*', 'user = ${params.Bvt_User}' } |
                            Set-Content \$configFile
                            echo "BVT User : ${params.Bvt_User}"
                            
                            (Get-Content \$configFile) |
                            ForEach-Object { \$_ -replace 'oc_verify\\s*=.*', 'oc_verify = ${params.OC_Verify}' } |
                            Set-Content \$configFile
                            echo "OC Commands verification : ${params.OC_Verify}"

                            (Get-Content \$configFile) |
                            ForEach-Object { \$_ -replace 'quick_burn_pwd\\s*=.*', 'quick_burn_pwd = ${params.QuickBurnPassword}' } |
                            Set-Content \$configFile
                            echo "Quick burn cluster password : ${params.QuickBurnPassword}"

                            (Get-Content \$configFile) |
                            ForEach-Object { \$_ -replace 'quick_fyre_pwd\\s*=.*', 'quick_fyre_pwd = ${params.RootPassword}' } |
                            Set-Content \$configFile

                            (Get-Content \$configFile) |
                            ForEach-Object { \$_ -replace 'multildap\\s*=.*', 'multildap = ${params.Multildap}' } |
                            Set-Content \$configFile
                            echo "Multildap Deployemnt : ${params.Multildap}"

                        """

                        withCredentials([usernamePassword(credentialsId: 'github-credentials', usernameVariable: 'GITHUB_USER', passwordVariable: 'GITHUB_PASS')]) {
                            def git_username = "${GITHUB_USER}"
                            def git_password = "${GITHUB_PASS}"
                        
                            powershellScript += """
                                echo "Setting github credentials..."
                                \$git_user = "${git_username}"
                                (Get-Content \$configFile) |
                                ForEach-Object { \$_ -replace 'git_user\\s*=.*', "git_user = \$git_user" } |
                                Set-Content \$configFile
                                echo "Setted git username"
                                
                                \$git_pwd = "${git_password}"
                                (Get-Content \$configFile) |
                                ForEach-Object { \$_ -replace 'git_pwd\\s*=.*', "git_pwd = \$git_pwd" } |
                                Set-Content \$configFile
                                echo "Setted git password"
                            """
                        }
                        
                        // Write PowerShell script content to a file
                        echo "Writing PowerShell script content to a file"
                        writeFile file: 'modify_config.ps1', text: powershellScript
                        
                         bat '''
                            echo Copying modify_config.ps1 contents to desktop file
                            scp -o StrictHostKeyChecking=no modify_config.ps1  C:\\Users\\Administrator\\Desktop
                        '''
                        
                        // Execute PowerShell script remotely via PowerShell Remoting
                        echo "Execute PowerShell script remotely via PowerShell Remoting..."
                        def result = powershell(script: """
                            Invoke-Command -ScriptBlock {
                                Invoke-Expression 'powershell -ExecutionPolicy Bypass -File C:\\Users\\Administrator\\Desktop\\modify_config.ps1'
                            } | Out-String
                        """, returnStdout: true).trim()
                        
                        // Print the output of the script execution
                        echo result
    
                        // Execute BVT remotely via PowerShell Remoting and capture output
                        echo "Execute BVT remotely via PowerShell Remoting..."
                        def bvtResult = powershell(script: """
                            \$session = New-PSSession
                            Invoke-Command -Session \$session -ScriptBlock {
                                Invoke-Expression 'cmd /c "cd C:\\CP4BA_BVT_Automation\\Cp4ba-Automation\\CP4BA_Package && python runner.py"'
                            } | Out-String
                            Remove-PSSession -Session \$session
                        """, returnStdout: true).trim()
    
                        // Print the output of the BVT execution
                        echo bvtResult
                        
                        // Copy the reports back to the workspace
                        bat """
                            echo Copying reports back to Jenkins workspace...
                            pscp  -pw Admin@123123123 \\\\${selectedAgent}\\C\$\\CP4BA_BVT_Automation\\Cp4ba-Automation\\CP4BA_Package\\reports\\generated_reports\\${bvtreport}_${params.ProjectName}_${params.DeploymentType}_${cluster}*.pdf  root@cp4ba-jenkins1.fyre.ibm.com:/home/jenkins/jenkins/jenkins_home/workspace/BVT_Automation
                            pscp  -pw Admin@123123123 \\\\${selectedAgent}\\C\$\\CP4BA_BVT_Automation\\Cp4ba-Automation\\CP4BA_Package\\reports\\generated_reports\\${mvtreport}_${params.ProjectName}_${params.DeploymentType}_${cluster}*.pdf  root@cp4ba-jenkins1.fyre.ibm.com:/home/jenkins/jenkins/jenkins_home/workspace/BVT_Automation 
                            pscp  -pw Admin@123123123 \\\\${selectedAgent}\\C\$\\CP4BA_BVT_Automation\\Cp4ba-Automation\\CP4BA_Package\\reports\\generated_reports\\*.xml  root@cp4ba-jenkins1.fyre.ibm.com:/home/jenkins/jenkins/jenkins_home/workspace/BVT_Automation 
                        """   
                        
                    }     
                }      
            }
        }

        stage('Get Cluster Data') {
            steps {
		        withCredentials([usernamePassword(credentialsId: 'github-credentials', usernameVariable: 'GITHUB_USER', passwordVariable: 'GITHUB_PASS')]) {
                    node('master'){
                    script {

                        if (params.QuickBurn == "yes") {
                            cluster = params.QuickBurnName.toLowerCase()
                            env.KUBE_PASS = params.QuickBurnPassword
                            env.ocp = params.QuickBurnVersion
                            env.ROOT_PASSWORD = params.RootPassword
                            env.SSH_URL = "api.${cluster}.cp.fyre.ibm.com"

                        } else {
                            // URL to the JSON file
                            sh('curl -u ${GITHUB_USER}:${GITHUB_PASS} -o /tmp/clusters_data.json https://raw.github.ibm.com/dkrishan/Cp4ba-Automation/main/CP4BA_Package/clusters.json')

                            // Parse the JSON content
                            def jsonSlurper = new groovy.json.JsonSlurper()
                            def inputFile = new File("/tmp/clusters_data.json")
                            def jsonString = inputFile.text
                            def jsonData = jsonSlurper.parseText(jsonString)
                            cluster = params.ClusterName.toLowerCase()
                            env.ROOT_PASSWORD = jsonData[cluster].root_pwd
                            env.KUBE_PASS = jsonData[cluster].kube_pwd
                            env.ocp = jsonData[cluster].version
                            env.SSH_URL = "api.${cluster}.cp.fyre.ibm.com"
                            }
                        }
                    }
                }
            }
        }
    }

    post {
        success {
            withCredentials([usernamePassword(credentialsId: 'github-credentials', usernameVariable: 'GITHUB_USER', passwordVariable: 'GITHUB_PASS')]) {
                node('master'){
                    script {
                        def message = "BVT Succeeded for deployment in '${cluster}'.\nProjectName : ${params.ProjectName}.\nDeployment type : ${params.DeploymentType}.\nDatabase : ${params.DB}.\nLdap : ${params.LDAP}.\nLink to the Jenkins Job:\n${env.BUILD_URL}"
                        env.message = message
                        def status = "success"
                        env.status = status
                        build job: 'slack-notify', parameters: [
                            string(name:'Status',value:status),
                            string(name:'MESSAGE',value:message)]
                        archiveArtifacts artifacts: "${bvtreport}*.pdf, ${mvtreport}*.pdf , bvt*.xml", allowEmptyArchive: false
                        sh """
                            
                            oc login https://${env.SSH_URL}:6443 -u kubeadmin -p ${env.KUBE_PASS} --insecure-skip-tls-verify
                            oc project ${params.ProjectName}
                            name=\$(oc get configmap | grep access-info | awk \'{print \$1}\')
                            echo 'Configmap name: \$name'
                            oc get configmap \$name -o yaml > access.yaml 
                            ls
                            pwd
                        """
                        def yamlData = readYaml file: 'access.yaml'
                        def formattedString = ''
                        yamlData.data.each { key, value ->
                            // Append each key-value pair to the formatted string
                            if(key!="cpe-stateless-access-info"){
                            formattedString += "*${key}*:\n```${value}```\n\n"
                            }
                        }
                        def textFile = 'extracted-text.txt'
                        sh "pdftotext BVT_CP4BA_${params.ProjectName}_${params.DeploymentType}_${cluster}_2*.pdf ${textFile}"
                        def pdfText = readFile(textFile)
                        def consoleLink = (pdfText =~ /console link : (\S+)/)[0][1]
                        consoleLink+="(kubeadmin/${env.KUBE_PASS})"
                        def credentials = (pdfText =~ /Credentials : (\S+)/)[0][1]
                        
                        echo "Project Name: ${env.projectName}"
                        
                        def dbType = extractFirstMatch(pdfText, /(?i)Database\s*\n\s*(\w+)/)
                        echo "Database type: ${dbType}"

                        def ldapType = extractFirstMatch(pdfText, /(?i)LDAP\s*\n\s*(\w+)/)
                        echo "LDAP type: ${ldapType}"

                        def fips = (pdfText =~ /Fips : (\S+)/)[0][1]
                        def egressNetworkPolicy = (pdfText =~ /Egress Network Policy : (\S+)/)[0][1]
                        def productsStart = pdfText.indexOf('Products') + 'Products'.length()
                        def productsEnd = pdfText.indexOf('Test Cases', productsStart)
                        def productsText = pdfText.substring(productsStart, productsEnd).trim()
                        def ProductList = productsText.split('\n').collect { it.trim() }.findAll { it }.join(',')
                        
                        echo "Products: ${ProductList}"

                        def baseArtifactUrl = "${env.JENKINS_URL}job/${env.JOB_NAME}/${env.BUILD_NUMBER}/artifact/"
                        def artifactUrls = ""
                        
                        // List artifacts through Jenkins API or build workspace directly
                        def artifacts = sh(script: "ls -1 ${env.WORKSPACE}", returnStdout: true).trim().split('\n')
                        artifacts.each { fileName ->
                            if (fileName.startsWith("BVT_CP4BA_${params.ProjectName}_${params.DeploymentType}_${cluster}_2")) {
                                def url = "${baseArtifactUrl}${fileName}"
                                artifactUrls+=url
                            }
                        }
                        def baseArtifactUrl2 = "${env.JENKINS_URL}job/${env.JOB_NAME}/${env.BUILD_NUMBER}/artifact/"
                        def artifactUrls2 = ""
                        
                        // List artifacts through Jenkins API or build workspace directly
                        def artifacts2 = sh(script: "ls -1 ${env.WORKSPACE}", returnStdout: true).trim().split('\n')
                        artifacts2.each { fileName ->
                            if (fileName.startsWith("MVT_CP4BA_${params.ProjectName}_${params.DeploymentType}_${params.ClusterName}_2")) {
                                def url = "${baseArtifactUrl2}${fileName}"
                                artifactUrls2+=url
                            }
                        }
                        
                        echo "${artifactUrls2}"
                        def hellomessage = "Hi All,\nHere is the Fresh ${params.DeploymentType} deployment for CP4BA Content Pattern ${params.Build} ${params.IFixVersion}  Build"
                        def message2 = hellomessage + "\nBVT : ${artifactUrls}\nMVT: ${artifactUrls2}\n\nConsole Url: " +consoleLink+"\nProject Name: "+params.ProjectName+"\nProducts: "+ProductList+"\nCredentials: "+ credentials+"\nfips: "+fips+"\nNetwork Policy: "+egressNetworkPolicy+"\nDatabase: "+dbType+"\nLdap: "+ldapType+"\n*Access URL*:\n"+formattedString
                        
			slackSend (color: '#00FF00', message: message2)
                        sh """
                            sshpass -p 'Admin@123123123' ssh -o StrictHostKeyChecking=no root@cp4ba-jenkins1.fyre.ibm.com '
                            cd /home/jenkins/jenkins/jenkins_home/workspace/BVT_Automation && \
                            rm -rf * && \
                            cd /opt
                            '
                        """
                        
                    }
                }
            }
        }
        failure {
            script {
                def message = "BVT failed for Deployment in '${cluster}'.\nProjectName : ${params.ProjectName}.\nDeployment type : ${params.DeploymentType}.\nDatabase : ${params.DB}.\nLdap : ${params.LDAP}.\nLink to the Jenkins Job:\n${env.BUILD_URL}"
                env.message = message
                def status = "failed"
                env.status = status
                build job: 'slack-notify', parameters: [
                    string(name:'Status',value:status),
                    string(name:'MESSAGE',value:message)]

                sh """
                    sshpass -p 'Admin@123123123' ssh -o StrictHostKeyChecking=no root@cp4ba-jenkins1.fyre.ibm.com '
                    cd /home/jenkins/jenkins/jenkins_home/workspace/BVT_Automation && \
                    rm -rf * && \
                    cd /opt
                    '
                """
            }
        }
        always {
            node('master') {
            script{
            echo "Reports and outputs archived."
            }
            }
        }
    }
}

