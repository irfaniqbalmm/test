#!/bin/bash

function save_log(){
    LOG_FILE="./logs/Resource-status-$(date +'%Y%m%d%H%M%S').log"

    # Create a named pipe
    PIPE=$(mktemp -u)
    mkfifo "$PIPE"

    # Tee the output to both the log file and the terminal
    tee "$LOG_FILE" < "$PIPE" &

    # Redirect stdout and stderr to the named pipe
    exec > "$PIPE" 2>&1

    # Remove the named pipe
    rm "$PIPE"
}

function chk_resources() {

    # Get all namespaces
    # namespaces=$(oc  get ns --no-headers -o custom-columns=":metadata.name")

    # Get from supplied namespaces
    namespaces=$1
    for ns in $namespaces; do
    echo -e "\nNamespace: $ns"
    echo "Timestamp: $(date)"

    # Checking pods
    echo "Pods:"
    pods=$(oc  get pods -n "$ns" --no-headers | grep -E 'Error|CrashLoopBackOff|ImagePullBackOff|Pending|Failed')
    if [ -n "$pods" ]; then
        echo "$pods"
        while read -r pod_line; do
        pod_name=$(echo "$pod_line" | awk '{print $1}')
        echo -e "\nDescribing pod: $pod_name"
        oc  describe pod "$pod_name" -n "$ns"
        done <<< "$pods"
    else
        echo "No pod issues"
    fi

    # Checking deployments
    echo "Deployments:"
    deployments=$(oc  get deploy -n "$ns" --no-headers | grep -E '0/[0-9]+|Unavailable')
    if [ -n "$deployments" ]; then
        echo "$deployments"
        while read -r deploy_line; do
        deploy_name=$(echo "$deploy_line" | awk '{print $1}')
        echo -e "\nDescribing deployment: $deploy_name"
        oc  describe deploy "$deploy_name" -n "$ns"
        done <<< "$deployments"
    else
        echo "No deployment issues"
    fi

    # Checking daemonsets
    echo "DaemonSets:"
    ds=$(oc  get ds -n "$ns" --no-headers | grep -E '0/[0-9]+|Unavailable')
    if [ -n "$ds" ]; then
        echo "$ds"
        while read -r ds_line; do
        ds_name=$(echo "$ds_line" | awk '{print $1}')
        echo -e "\nDescribing daemonset: $ds_name"
        oc  describe ds "$ds_name" -n "$ns"
        done <<< "$ds"
    else
        echo "No daemonset issues"
    fi

    # Checking statefulsets
    echo "StatefulSets:"
    sts=$(oc  get sts -n "$ns" --no-headers | grep -E '0/[0-9]+|Unavailable')
    if [ -n "$sts" ]; then
        echo "$sts"
        while read -r sts_line; do
        sts_name=$(echo "$sts_line" | awk '{print $1}')
        echo -e "\nDescribing statefulset: $sts_name"
        oc  describe sts "$sts_name" -n "$ns"
        done <<< "$sts"
    else
        echo "No statefulset issues"
    fi

    # Checking jobs
    echo "Jobs:"
    jobs=$(oc  get jobs -n "$ns" --no-headers | grep -E '0/[0-9]+|Failed')
    if [ -n "$jobs" ]; then
        echo "$jobs"
        while read -r job_line; do
        job_name=$(echo "$job_line" | awk '{print $1}')
        echo -e "\nDescribing job: $job_name"
        oc  describe job "$job_name" -n "$ns"
        done <<< "$jobs"
    else
        echo "No job issues"
    fi

    # Checking events
    echo "Events:"
    events=$(oc  get events -n "$ns" --field-selector type!=Normal --sort-by='.lastTimestamp' | grep -E 'Warning|Error|Failed|Fatal')
    if [ -n "$events" ]; then
        echo "$events"
    else
        echo "No critical events"
    fi
    done

    echo -e "\nDiagnostics completed at: $(date)"

    echo -e "\n=========Fetching logs from ibm-content-operator (Ansible Artifacts) ========="
    oc -n $2 exec -it $(oc get pod -n $2 | grep ibm-content-operator | awk '{print $1}') -c operator -- sh -c "find /tmp/ansible-operator/runner/icp4a.ibm.com/v1/Content/*/*/artifacts/ -name stdout | xargs cat | grep -Ei 'failed|error|warning|fatal' | sed -E 's/(failed|error|fatal|warning)/\x1b[31m\1\x1b[0m/g'"

    echo -e "\n========= Fetching logs from ibm-content-operator (Container Logs) ========="
    oc logs $(oc get pod -n $2 | grep ibm-content-operator | awk '{print $1}') -c operator | grep -Ei 'failed|error|warning|fatal' | sed -E 's/(failed|error|fatal|warning)/\x1b[31m\1\x1b[0m/gI'
}


save_log

# get content.yaml from ocp
oc login https://api.$1.cp.fyre.ibm.com:6443 -u kubeadmin -p $2 --insecure-skip-tls-verify && \
echo "https://api.$1.cp.fyre.ibm.com:6443"
oc project $3
echo "project $3"

oc get Content -o yaml > content.yaml

# call the python function and print statuses
echo "Running validation check..."
output=$(python3 validate.py | tee /tmp/validate_output.txt)
result=$(tail -n 1 /tmp/validate_output.txt)  # Get last line: SUCCESS or FAILURE
deployment=0
#To loop for 18 times(10 minute interval 15 times means 2.5 hours)
start=16
while [[ $start -ge 1 ]]
do
    if [[ "$result" != "SUCCESS" ]]; then
        echo "Deployment not completed. Retrying in 10 minutes..."
        oc login https://api.$1.cp.fyre.ibm.com:6443 -u kubeadmin -p $2 --insecure-skip-tls-verify && \
        oc project $3
        echo "project $3"
        oc get Content -o yaml > content.yaml
        # call the python function
        output=$(python3 validate.py | tee /tmp/validate_output.txt)
        result=$(tail -n 1 /tmp/validate_output.txt)
        # remove content.yaml
        rm -rf content.yaml

        #verify pull-secret error during the deployment
        python3 pull_secret.py
        if [[ $? -ne 0 ]]; then  # Check the exit code of the Python script
            echo "ImagePullBackOff error in pods. Terminating the pipeline execution"
            # exit 0
        fi

        echo "####################### Checking the resources ########################"
        chk_resources $3 $4
        echo "Deployment is in progress. $((start -= 1)) retries left. Next retry in 10 minutes"
        echo "#########################################################################################"
        sleep 10m
    else
        deployment=1
        echo "Deployment is Done"
        break
    fi

done

if [ $deployment -eq 0 ]; then
    echo "Deployment Failed, Components Not Ready"
    cat /tmp/validate_output.txt  # Show statuses on failure
    exit 1 
fi
echo "$(date) :- Deployment completed. Waiting for 30 minutes before proceeding...."
sleep 30m

#Adding 30m more in case of 2500 and starter deployment
type=$(oc get content --no-headers | awk '{print $1}')
if [[ $type  == "icp4adeploy" ]]; then
    version=$(oc get content icp4adeploy  -n $3  -o jsonpath="{.spec.appVersion}")
    if [[ "$version" == "25.0.0" ]]; then
        echo "Waitging 30 minutes more in case of 2500 and starter deployment"
        sleep 30m
    fi
fi


echo "$(date) :- Waited for 30 minutes. Proceeding with the deployment....."
echo "Deployment Completed Successfully"
exit 1
