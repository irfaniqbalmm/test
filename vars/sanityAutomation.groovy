
def selectedAgent = null

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
        iccsapReport = 'iccsap_sanity_tests_report'
        ierReport = 'ier_sanity_tests_report'
        cpeReport = 'cpe_sanity_tests_report'
        GITHUB_CREDS = credentials('github-credentials')
    }
    stages {
        stage('Select Build Agent') {
            steps {
                script {
                    def agents = ['bvt1', 'bvtauto1']

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
                }
            }
        }

        stage('Logging Parameter Summary') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'github-credentials', usernameVariable: 'GITHUB_USER', passwordVariable: 'GITHUB_PASS'), string(credentialsId: 'jenkinsPassword', variable: 'jenkinsPassword'), string(credentialsId: 'entitlement_prod', variable: 'entitlement_prod'), string(credentialsId: 'pull_secret_token', variable: 'pull_secret_token')]) {
                    script {
                        echo "Cluster Name: ${params.Cluster}"
                        echo "Namespace: ${params.Namespace}"
                        env.jenkinspwd = jenkinsPassword
                        echo "JenkinsPWDDDD ${env.jenkinspwd}"
                        echo "Date: ${params.Date}"
                        echo "Deployment Type: ${params.deploymenttype}"
                        echo "Functionality: ${params.Functionality}"
                        currentBuild.displayName = "${params.ClusterName}-${params.ProjectName}-${selectedAgent}-${params.Build}-${params.IFixVersion}"
                        echo "Current build name: ${currentBuild.displayName}"
                        }
                }
            }
        }

        stage('Configure and Prepare Agent'){
            steps{
                script{
                    node(selectedAgent) {
                        echo "Getting latest BVT Code..."
                        bat '''
                            cd C:\\CP4BA_BVT_Automation
                            python "git_pull&open.py"
                        '''
                        
                        // Define PowerShell script content
                        def powershellScript = """
                            \$configFile = 'C:\\CP4BA_BVT_Automation\\Cp4ba-Automation\\CP4BA_Package\\component_sanity_tests\\config\\config.ini'
                            
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
                            
                        """
                        
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

                        echo "Executing sanity.main file to prepare the agent."
                        bat """
                            cd C:\\CP4BA_BVT_Automation\\Cp4ba-Automation\\CP4BA_Package
                            python "component_sanity_tests/sanity_main.py"
                        """
                    }
                }
            }
        }

        stage('Execute ICCSAP sanity tests'){
            when {
                expression {
                    return params.Components.tokenize(',').contains('ICCSAP')
                }
            }
            steps{
                script{
                    node(selectedAgent){

                        // Executing iccsap_main.py
                        powershell(script: """
                            \$session = New-PSSession
                            Invoke-Command -Session \$session -ScriptBlock {
                                Invoke-Expression 'cmd /c "cd C:\\CP4BA_BVT_Automation\\Cp4ba-Automation\\CP4BA_Package && python component_sanity_tests/iccsap_main.py"'
                            } | Out-String
                            Remove-PSSession -Session \$session
                        """)
                        
                        // Copy the reports back to the workspace
                        bat """
                            echo Copying reports back to Jenkins workspace...
                            pscp  -pw ${env.jenkinspwd} \\\\${selectedAgent}\\C\$\\CP4BA_BVT_Automation\\Cp4ba-Automation\\CP4BA_Package\\component_sanity_tests\\reports\\iccsap\\generated_reports\\iccsap_sanity_tests_report.pdf  "root@cp4ba-jenkins1.fyre.ibm.com:/home/jenkins/jenkins/jenkins_home/workspace/9.ComponentSanityTestsAutomation/"
                        """   
                        
                    }     
                }      
            }
        } 
        stage('Execute IER sanity tests'){
                when {
                    expression {
                        return params.Components.tokenize(',').contains('IER')
                    }
                }
                steps{
                    script{
                        node(selectedAgent){
    
                            // Executing ier_main.py
                            powershell(script: """
                                \$session = New-PSSession
                                Invoke-Command -Session \$session -ScriptBlock {
                                    Invoke-Expression 'cmd /c "cd C:\\CP4BA_BVT_Automation\\Cp4ba-Automation\\CP4BA_Package && python component_sanity_tests/ier_main.py"'
                                } | Out-String
                                Remove-PSSession -Session \$session
                            """)
                            
                            // Copy the reports back to the workspace
                            bat """
                                echo Copying reports back to Jenkins workspace...
                                pscp -pw ${env.jenkinspwd} \\\\${selectedAgent}\\C\$\\CP4BA_BVT_Automation\\Cp4ba-Automation\\CP4BA_Package\\component_sanity_tests\\reports\\ier\\generated_reports\\ier_sanity_tests_report.pdf "root@cp4ba-jenkins1.fyre.ibm.com:/home/jenkins/jenkins/jenkins_home/workspace/9.ComponentSanityTestsAutomation/"
                            """
                            
                        }     
                    }      
                }
            } 
        stage('Execute CPE sanity tests'){
            when {
                expression {
                    return params.Components.tokenize(',').contains('CPE')
                }
            }
            steps{
                script{
                    node(selectedAgent){

                        // Executing cpe.py
                        powershell(script: """
                            \$session = New-PSSession
                            Invoke-Command -Session \$session -ScriptBlock {
                                Invoke-Expression 'cmd /c "cd C:\\CP4BA_BVT_Automation\\Cp4ba-Automation\\CP4BA_Package && python component_sanity_tests/tests/cpe.py"'
                            } | Out-String
                            Remove-PSSession -Session \$session
                        """)
                        
                        // Copy the reports back to the workspace
                        bat """
                            echo Copying reports back to Jenkins workspace...
                            pscp  -pw ${env.jenkinspwd} \\\\${selectedAgent}\\C\$\\CP4BA_BVT_Automation\\Cp4ba-Automation\\CP4BA_Package\\component_sanity_tests\\reports\\cpe\\generated_reports\\cpe_sanity_tests_report.pdf  "root@cp4ba-jenkins1.fyre.ibm.com:/home/jenkins/jenkins/jenkins_home/workspace/9.ComponentSanityTestsAutomation/"
                        """   
                        
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
                        def message = "Sanity tests completed for deployment in '${params.ClusterName.toLowerCase()}'.\nProjectName : ${params.ProjectName}.\nDeployment type : ${params.DeploymentType}.\nLink to the Jenkins Job:\n${env.BUILD_URL}"
                        env.message = message
                        def status = "success"
                        env.status = status
                        build job: 'slack-notify', parameters: [
                            string(name:'Status',value:status),
                            string(name:'MESSAGE',value:message)]
                        archiveArtifacts artifacts: "${iccsapReport}*.pdf, ${ierReport}*.pdf, ${cpeReport}*.pdf", allowEmptyArchive: false
                        
                        echo "Products: ${params.Components}"
                        echo "Project Name: ${env.projectName}"
                        def baseArtifactUrl = "${env.JENKINS_URL}job/${env.JOB_NAME}/${env.BUILD_NUMBER}/artifact/"
                        def artifactUrls = ""
                        
                        // List artifacts through Jenkins API or build workspace directly
                        def artifacts = sh(script: "ls -1 \"${env.WORKSPACE}\"", returnStdout: true).trim().split('\n')
                        artifacts.each { fileName ->
                            if (fileName.startsWith("${iccsapReport}")) {
                                def url = "${baseArtifactUrl}${fileName}"
                                artifactUrls+=url
                            }
                            if (fileName.startsWith("${ierReport}")) {
                                def url = "${baseArtifactUrl}${fileName}"
                                artifactUrls+="\n$url"
                            }
                            if (fileName.startsWith("${cpeReport}")) {
                                def url = "${baseArtifactUrl}${fileName}"
                                artifactUrls+=url
                            }
                        }
                        
                        echo "${artifactUrls}"
                        def hellomessage = "Hi All,\nHere are the Sanity Tests Reports for ${params.DeploymentType} Deployment of ${params.Build} ${params.IFixVersion} Build"
                        def message2 = hellomessage + "\nReports :\n ${artifactUrls}\n\nProject Name: "+params.ProjectName+"\nProducts: "+params.Components
                        
			    slackSend (color: '#00FF00', message: message2)
                        sh """
                            sshpass -p ${env.jenkinspwd} ssh -o StrictHostKeyChecking=no root@cp4ba-jenkins1.fyre.ibm.com '
                            cd "/home/jenkins/jenkins/jenkins_home/workspace/9.ComponentSanityTestsAutomation" && \
                            rm -rf * && \
                            cd /opt
                            '
                        """
                        echo "Workspace cleaned after successful archiving."
                    }
                }
            }
        }

        failure {
            script {
                def message = "Sanity tests failed for deployment in '${params.ClusterName.toLowerCase()}'.\nProjectName : ${params.ProjectName}.\nDeployment type : ${params.DeploymentType}.\nLink to the Jenkins Job:\n${env.BUILD_URL}"
                env.message = message
                def status = "failed"
                env.status = status
                build job: 'slack-notify', parameters: [
                    string(name:'Status', value:status),
                    string(name:'MESSAGE', value:message)]

                sh """
                    sshpass -p ${env.jenkinspwd} ssh -o StrictHostKeyChecking=no root@cp4ba-jenkins1.fyre.ibm.com '
                    cd "/home/jenkins/jenkins/jenkins_home/workspace/9.ComponentSanityTestsAutomation" && \
                    rm -rf * && \
                    cd /opt
                    '
                """
                echo "Workspace cleaned."
            }
        }

        always {
            echo "All done! Sanity tests execution completed!!"
        }   
    }
}