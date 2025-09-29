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

pipeline {
    agent none
    environment {
        mvtreport = "MVT_${params.Product}"
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
                    currentBuild.displayName = "${params.ClusterName}-${params.ProjectName}-${selectedAgent}-${params.Build}-${params.IFixVersion}"
                    node(selectedAgent) {
                        
                        if (params.QuickBurn == "Yes") {
                            cluster = params.QuickBurnName.toLowerCase()
                            echo "MVT running for a deployment in quick burn cluster ${cluster}..."
                            env.KUBE_PASS = params.QuickBurnPassword
                            env.ocp = params.QuickBurnVersion
                            env.ROOT_PASSWORD = params.RootPassword
                            env.SSH_URL = "api.${cluster}.cp.fyre.ibm.com"
                        } else {
                            cluster = params.ClusterName
                        }

                        echo "Running build on agent: ${selectedAgent}"
                        
                        echo "Getting Latest MVT Code..."
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
                            ForEach-Object { \$_ -replace 'deployment_type\\s*=.*', 'deployment_type = ${params.DeploymentType}' } |
                            Set-Content \$configFile
                            echo "Deployment type : ${params.DeploymentType}"
                            
                            (Get-Content \$configFile) |
                            ForEach-Object { \$_ -replace 'quick_burn_pwd\\s*=.*', 'quick_burn_pwd = ${params.QuickBurnPassword}' } |
                            Set-Content \$configFile
                            echo "Quick burn cluster password : ${params.QuickBurnPassword}"

                            (Get-Content \$configFile) |
                            ForEach-Object { \$_ -replace 'quick_fyre_pwd\\s*=.*', 'quick_fyre_pwd = ${params.RootPassword}' } |
                            Set-Content \$configFile

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
    
                        // Execute MVT remotely via PowerShell Remoting and capture output
                        echo "Execute MVT remotely via PowerShell Remoting..."
                        def mvtResult = powershell(script: """
                            \$session = New-PSSession
                            Invoke-Command -Session \$session -ScriptBlock {
                                Invoke-Expression 'cmd /c "cd C:\\CP4BA_BVT_Automation\\Cp4ba-Automation\\CP4BA_Package && python mvt_runner.py ${params.Product}"'
                            } | Out-String
                            Remove-PSSession -Session \$session
                        """, returnStdout: true).trim()
    
                        // Print the output of the MVT execution
                        echo mvtResult
                        
                        // Copy the reports back to the workspace
                        bat """
                            echo Copying reports back to Jenkins workspace...
                            pscp  -pw Admin@123123123 \\\\${selectedAgent}\\C\$\\CP4BA_BVT_Automation\\Cp4ba-Automation\\CP4BA_Package\\reports\\generated_reports\\${mvtreport}_${params.ProjectName}_${params.DeploymentType}_${cluster}*.pdf  root@cp4ba-jenkins1.fyre.ibm.com:/home/jenkins/jenkins/jenkins_home/workspace/10.MVT_Automation 
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
                        def message = "MVT Succeeded for ${params.Product} deployment in '${cluster}'.\nProjectName : ${params.ProjectName}.\nDeployment type : ${params.DeploymentType}.\nLink to the Jenkins Job:\n${env.BUILD_URL}"
                        env.message = message
                        def status = "success"
                        env.status = status
                        build job: 'slack-notify', parameters: [
                            string(name:'Status',value:status),
                            string(name:'MESSAGE',value:message)]
                        archiveArtifacts artifacts: "${mvtreport}*.pdf", allowEmptyArchive: false
                        
                        
                        def baseArtifactUrl = "${env.JENKINS_URL}job/${env.JOB_NAME}/${env.BUILD_NUMBER}/artifact/"
                        def artifactUrls = ""
                        
                        // List artifacts through Jenkins API or build workspace directly
                        def artifacts = sh(script: "ls -1 ${env.WORKSPACE}", returnStdout: true).trim().split('\n')
                        artifacts.each { fileName ->
                            if (fileName.startsWith("MVT_${params.Product}_${params.ProjectName}_${params.DeploymentType}_${params.ClusterName}_2")) {
                                def url = "${baseArtifactUrl}${fileName}"
                                artifactUrls+=url
                            }
                        }
                        echo "${artifactUrls}"
                        def hellomessage = "Hi All,\nHere is the Fresh ${params.DeploymentType} deployment for CP4BA Content Pattern ${params.Build} ${params.IFixVersion}  Build"
                        def message2 = hellomessage + "MVT: ${artifactUrls2}\n\nProject Name: "+params.ProjectName+"\n"
                        
			slackSend (color: '#00FF00', message: message2)
                        sh """
                            sshpass -p 'Admin@123123123' ssh -o StrictHostKeyChecking=no root@cp4ba-jenkins1.fyre.ibm.com '
                            cd /home/jenkins/jenkins/jenkins_home/workspace/10.MVT_Automation && \
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
                def message = "MVT failed for ${params.Product} Deployment in '${cluster}'.\nProjectName : ${params.ProjectName}.\nDeployment type : ${params.DeploymentType}.\nLink to the Jenkins Job:\n${env.BUILD_URL}"
                env.message = message
                def status = "failed"
                env.status = status
                build job: 'slack-notify', parameters: [
                    string(name:'Status',value:status),
                    string(name:'MESSAGE',value:message)]

                sh """
                    sshpass -p 'Admin@123123123' ssh -o StrictHostKeyChecking=no root@cp4ba-jenkins1.fyre.ibm.com '
                    cd /home/jenkins/jenkins/jenkins_home/workspace/10.MVT_Automation && \
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

