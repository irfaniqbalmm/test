#!/bin/bash

function save_log(){
    LOG_FILE="Resource-status-$(date +'%Y%m%d%H%M%S').log"

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

save_log

echo "Starting cluster diagnostics at: $(date)"

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
oc exec -it $(oc get pod | grep ibm-content-operator | awk '{print $1}') -c operator -- sh -c "find /tmp/ansible-operator/runner/icp4a.ibm.com/v1/Content/*/*/artifacts/ -name stdout | xargs cat | grep -Ei 'failed|error|warning|fatal' | sed -E 's/(failed|error|fatal|warning)/\x1b[31m\1\x1b[0m/g'"

echo -e "\n========= Fetching logs from ibm-content-operator (Container Logs) ========="
oc logs $(oc get pod | grep ibm-content-operator | awk '{print $1}') -c operator | grep -Ei 'failed|error|warning|fatal' | sed -E 's/(failed|error|fatal|warning)/\x1b[31m\1\x1b[0m/gI'
