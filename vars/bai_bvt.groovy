def findFirstAvailableNode(agents) {
    for (agent in agents) {
        def node = Jenkins.instance.getNode(agent)
        echo "The node instance is ${node}"
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

pipeline {
    agent none
    environment {
        bvtreport = 'BVT_BAI'
        mvtreport = 'MVT_BAIS'
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
                    currentBuild.displayName = "${params.ClusterName}-${params.ProjectName}-${selectedAgent}-${params.LDAP}-${params.Build}-${params.IFixVersion}"
                    node(selectedAgent) {

                        echo "Running build on agent: ${selectedAgent}"
                        
                        echo "Getting Latest BVT Code..."
                        bat '''
                            cd C:\\CP4BA_BVT_Automation
                            python "git_pull&open.py"
                        '''
                        
                        // Define PowerShell script content
                        def powershellScript = """
                            \$configFile = 'C:\\CP4BA_BVT_Automation\\Cp4ba-Automation\\CP4BA_Package\\BAI_BVT\\resources\\config.ini'
                            
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
                            ForEach-Object { \$_ -replace 'ldap\\s*=.*', 'ldap = ${params.LDAP}' } |
                            Set-Content \$configFile
                            echo "LDAP : ${params.LDAP}"
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
                        
                        // // Print the output of the script execution
                        echo result
    
                        // Execute BVT remotely via PowerShell Remoting and capture output
                        echo "Execute BVT remotely via PowerShell Remoting..."
                        def bvtResult = powershell(script: """
                            \$session = New-PSSession
                            Invoke-Command -Session \$session -ScriptBlock {
                                Invoke-Expression 'cmd /c "cd /d C:\\CP4BA_BVT_Automation\\Cp4ba-Automation\\CP4BA_Package && python BAI_BVT\\bai_runner.py"'
                            } | Out-String
                            Remove-PSSession -Session \$session
                        """, returnStdout: true).trim()
    
                        // Print the output of the BVT execution
                        // echo bvtResult
                        cluster = params.ClusterName.toLowerCase()
                        echo "cluster name: ${cluster}"
                        // Copy the reports back to the workspace
                        bat """
                            echo Copying reports back to Jenkins workspace...
                            pscp -pw Admin@123123123 \\\\${selectedAgent}\\C\$\\CP4BA_BVT_Automation\\Cp4ba-Automation\\CP4BA_Package\\BAI_BVT\\reports\\generated_reports\\${bvtreport}_${params.ProjectName}_production_${cluster}*.pdf  root@cp4ba-jenkins1.fyre.ibm.com:/home/jenkins/jenkins/jenkins_home/workspace/7.BAI_Standalone_BVT_Auto
                            pscp -pw Admin@123123123 \\\\${selectedAgent}\\C\$\\CP4BA_BVT_Automation\\Cp4ba-Automation\\CP4BA_Package\\BAI_BVT\\reports\\generated_reports\\${mvtreport}_${params.ProjectName}_production_${cluster}*.pdf  root@cp4ba-jenkins1.fyre.ibm.com:/home/jenkins/jenkins/jenkins_home/workspace/7.BAI_Standalone_BVT_Auto
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
                        // URL to the JSON file
                        sh('curl -u ${GITHUB_USER}:${GITHUB_PASS} -o /tmp/clusters_data.json https://raw.github.ibm.com/dkrishan/Cp4ba-Automation/main/CP4BA_Package/clusters.json')

                        // Parse the JSON content
                        def jsonSlurper = new groovy.json.JsonSlurper()
                        def inputFile = new File("/tmp/clusters_data.json")
                        def jsonString = inputFile.text
                        def jsonData = jsonSlurper.parseText(jsonString)
                        env.cluster = params.ClusterName.toLowerCase()
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

    post {
        success {
            withCredentials([usernamePassword(credentialsId: 'github-credentials', usernameVariable: 'GITHUB_USER', passwordVariable: 'GITHUB_PASS')]) {
                node('master'){
                    script {
                        def message = "BAI Standalone BVT Succeeded for deployment in '${cluster}'.\nProjectName : ${params.ProjectName}.\nLdap : ${params.LDAP}.\nLink to the Jenkins Job:\n${env.BUILD_URL}"
                        env.message = message
                        def status = "success"
                        env.status = status
                        build job: 'slack-notify', parameters: [
                            string(name:'Status',value:status),
                            string(name:'MESSAGE',value:message)]

                        // Archiving reports
                        archiveArtifacts artifacts: "${bvtreport}*.pdf", allowEmptyArchive: false
                        archiveArtifacts artifacts: "${mvtreport}*.pdf", allowEmptyArchive: false
                        
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
                            formattedString += "*${key}*:\n```${value}```\n\n"
                        }
                        def textFile = 'extracted-text.txt'
                        def pdfFilePattern = "BVT_BAI_${params.ProjectName}_production_${cluster}_2*.pdf"

                        // Ensure PDF file exists before processing
                        def fileExists = sh(script: "ls ${pdfFilePattern} 2>/dev/null", returnStatus: true) == 0
                        if (!fileExists) {
                            error "PDF file matching pattern '${pdfFilePattern}' not found!"
                        }
                        // Convert PDF to text
                        sh """
                            pdftotext ${pdfFilePattern} ${textFile}
                            echo "Extracted Text Content:"
                            cat ${textFile}  # Debugging step
                        """

                        // Read extracted text
                        def pdfText = readFile(textFile)

                        // Extract console link and credentials
                        def consoleLink = (pdfText =~ /console link : (\S+)/)[0][1]
                        consoleLink += "(kubeadmin/${env.KUBE_PASS})"
                        def credentials = (pdfText =~ /Credentials : (\S+)/)[0][1]

                        // // Extract Egress Network Policy safely
                        // def egressMatch = (pdfText =~ /Egress\s*Network\s*Policy\s*:\s*(\S+)/)
                        // if (egressMatch) {
                        //     def egressNetworkPolicy = egressMatch[0][1]
                        // } else {
                        //     error "Egress Network Policy not found in extracted text!"
                        // }

                        // Define product list
                        def ProductList = 'BAI Standalone'
                        echo "Products: ${ProductList}"
                        echo "Project Name: ${env.projectName}"
                        def baseArtifactUrl = "${env.JENKINS_URL}job/${env.JOB_NAME}/${env.BUILD_NUMBER}/artifact/"
                        def artifactUrls = ""
                        
                        // List artifacts through Jenkins API or build workspace directly
                        def artifacts = sh(script: "ls -1 ${env.WORKSPACE}", returnStdout: true).trim().split('\n')
                        artifacts.each { fileName ->
                            if (fileName.startsWith("BVT_BAI_${params.ProjectName}_production_${cluster}_2")) {
                                def url = "${baseArtifactUrl}${fileName}"
                                artifactUrls+=url
                            }
                        }

                        def baseArtifactUrl2 = "${env.JENKINS_URL}job/${env.JOB_NAME}/${env.BUILD_NUMBER}/artifact/"
                        def artifactUrls2 = ""
                        
                        // List artifacts through Jenkins API or build workspace directly
                        def artifacts2 = sh(script: "ls -1 ${env.WORKSPACE}", returnStdout: true).trim().split('\n')
                        artifacts2.each { fileName ->
                            if (fileName.startsWith("MVT_BAIS_${params.ProjectName}_production_${cluster}_2")) {
                                def url = "${baseArtifactUrl2}${fileName}"
                                artifactUrls2+=url
                            }
                        }
                        
                        echo "${artifactUrls2}"

                        def hellomessage = "Hi All,\nHere is the Fresh Production deployment for BAI(Business Automation Insights) ${params.Build} ${params.IFixVersion}  Build"
                        def message2 = hellomessage + "\nBVT : ${artifactUrls}\nMVT: ${artifactUrls2}\n\nConsole Url: " +consoleLink+"\nProject Name: "+params.ProjectName+"\nProducts: "+ProductList+"\nLdap: "+params.LDAP+"\nCredentials: "+ credentials +"\n\n*Access URL*:\n"+ formattedString
                        slackSend (color: '#00FF00', message: message2)
                        sh """
                            sshpass -p 'Admin@123123123' ssh -o StrictHostKeyChecking=no root@cp4ba-jenkins1.fyre.ibm.com '
                            cd /home/jenkins/jenkins/jenkins_home/workspace/7.BAI_Standalone_BVT_Auto && \
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
                def message = "BAI Standalone BVT failed for Deployment in '${cluster}'.\nProjectName : ${params.ProjectName}.\nLdap : ${params.LDAP}.\nLink to the Jenkins Job:\n${env.BUILD_URL}"
                env.message = message
                def status = "failed"
                env.status = status
                build job: 'slack-notify', parameters: [
                    string(name:'Status',value:status),
                    string(name:'MESSAGE',value:message)]

                sh """
                    sshpass -p 'Admin@123123123' ssh -o StrictHostKeyChecking=no root@cp4ba-jenkins1.fyre.ibm.com '
                    cd /home/jenkins/jenkins/jenkins_home/workspace/7.BAI_Standalone_BVT_Auto && \
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


