#!/bin/bash

function save_log(){
    LOG_FILE="restorelog-$(date +'%Y%m%d%H%M%S').log"

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

function chk_zen() {
    while true; do
        status=$(timeout 5 oc get zenservice -A -w -o yaml | grep -e 'InProgress' -e 'Failed')
        echo $status
        if [[ $status != "zenStatus: Completed" ]]; then
            echo "Zen service is in progress"
            timeout 5 oc get zenservice -A -w -o yaml | grep 'Progress'
        else
            echo "Zen service is Completed"
            timeout 5 oc get zenservice -A -w -o yaml | grep 'Completed'
        fi
    done
}


function shouldicontinue() {
    subname=$1
    while true; do
        printf "\x1B[1mDid we completed with  $subname  (Yes/No): \x1B[0m"
        read -rp "" ans
        case "$ans" in
        "y"|"Y"|"yes"|"Yes"|"YES")
            break
            ;;
        "n"|"N"|"no"|"No"|"NO")
            info "We need to complete before proceeding to next item $subname "
            ;;
        *)
            echo -e "Answer must be \"Yes\" or \"No\"\n"
            ;;
        esac
    done
}

#Saving the logs in a file
save_log
ns='cp250'
for i in $(oc get Restore -n velero  --no-headers | awk '{print $1}'); do
    echo "oc delete Restore $i"
	oc delete Restore $i -n velero --ignore-not-found=true --wait=true
done

rm -rf restore-*

#Deleting the catalogsource 
oc delete CatalogSource ibm-cert-manager-catalog -n ibm-cert-manager
oc delete CatalogSource ibm-licensing-catalog -n ibm-licensing

#deleting the operatorgroup
oc delete OperatorGroup ibm-cert-manager-operator -n ibm-cert-manager
oc delete OperatorGroup ibm-licensing-operator-app -n ibm-licensing

#deleting the ConfigMap
oc delete ConfigMap common-service-maps -n kube-public

#deleting the crd
oc delete  CustomResourceDefinition commonservices.operator.ibm.com 
oc delete  CustomResourceDefinition certmanagerconfigs.operator.ibm.com
oc delete  CustomResourceDefinition certificates.cert-manager.io
oc delete  CustomResourceDefinition issuers.cert-manager.io
oc delete  CustomResourceDefinition zenservices.zen.cpd.ibm.com
oc delete ZenService iaf-zen-cpdservice


oc delete Certificate opencontent-flink-operator-ca
oc delete Issuer cp4ba-rootca-issuer
oc delete Certificate content-insights-engine-flink-cert
oc delete Certificate cs-ca-certificate
oc delete Certificate iaf-system-automationui-aui-zen-cert
oc delete Issuer cp4ba-rootca-issuer
oc delete Issuer cs-ca-issuer
oc delete Issuer cs-ss-issuer
oc delete Issuer foundation-iaf-automationbase-ab-ss-issuer
oc delete Issuer iaf-system-automationui-aui-zen-issuer
oc delete Issuer iaf-system-automationui-aui-zen-ss-issuer
oc delete Issuer ibm-bts-ca-issuer-v1
oc delete Issuer ibm-bts-issuer-v1

#Deleting the ibm-licensing and cert namespace
oc delete Namespace ibm-cert-manager
oc delete Namespace ibm-licensing

function check_restore_status(){
    local resource=$1
    echo $resource
    echo "velero restore get | grep restore-$resource | awk '{ print $3}'"
    ocapply_status=$(velero restore get | grep restore-$resource | awk '{ print $3}')
    
    while true; do
        if [[ $ocapply_status == "Completed" ]]; then
            echo "Restore $ocapply_status is completed."
            velero restore describe restore-$resource --details
            chk_restore_status=$(velero restore describe restore-$resource --details | grep -e fail -e skip | wc -l)

            #Cheking the resource is having fail/skip in the o/p
            if [ $chk_restore_status -gt 0 ]; then
                echo "$resource have fail/skip in the o/p."
                # exit 1
            else
                echo "All good.. Proceeding"
            fi
            break
        else
            echo "Restore of $resource is in progress."
            sleep 5s 
            ocapply_status=$(velero restore get | grep restore-$resource | awk '{ print $3}')
        fi
    done
}

#getting the backup name from the velero backup get
echo "Checking the latest backup filename"
backup_name=$(velero backup get | grep 'commonservice' | cut -d ' ' -f 1 | head -n 1)

# Getting the backup file details
echo "Checking the latest backup done successfully or not"
backup_status=$(velero backup describe $backup_name --details | grep Phase)
if [[ $backup_status =~ "Completed" ]]; then
  echo "Backup $backup_name $backup_status "
fi

#Downloading the yaml files from the repo
# declare -a arr=("cs-db" "zen" "zen5-data")
declare -a arr=("namespace" "entitlementkey" "pull-secret" "catalog" "operatorgroup" "configmap" "crd" "commonservice" "singleton-subscriptions" "cert-manager" "subscriptions" "nss" "licensing" "operands")
# "cs-db" "zen" "zen5-data"
## now loop through the above array
for i in "${arr[@]}"
do
    echo -e "\n\n@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ Restore - start of resource $i @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"
    wget_status=$(wget --server-response wget https://raw.githubusercontent.com/IBM/ibm-common-service-operator/scripts-adopter/velero/restore/restore-$i.yaml 2>&1 | awk '/^  HTTP/{print $2}')
    echo "Wget status code of the restore-$i : $wget_status" 

    updatestatus=$(sed -i "s/__BACKUP_NAME__/$backup_name/g" ./restore-$i.yaml)
    echo "File ./restore-$i.yaml updated with $backup_name"

    if [[ $i =~ "pull-secret" ]]; then
        oc get secret pull-secret -n openshift-config -o yaml > original-pull-secret.yaml
        oc delete secret pull-secret -n openshift-config
    fi

    #Applying each yaml file
    oc_apply=$(oc apply -f restore-$i.yaml)
    echo $oc_apply

    #Checking the status of the restore
    if [[ $i =~ "singleton-subscriptions" ]]; then
        check_restore_status 'singleton-subscription'
    elif [[ $i =~ "subscription" ]]; then
        check_restore_status 'subscription'
    else
        check_restore_status $i
    fi
    

    if [[ $i =~ "namespace" ]]; then
         oc get namespace   

        # Moving to the specific project
        oc project $ns
    fi

    if [[ $i =~ "entitlementkey" ]]; then
         oc get secret   
    fi

    if [[ $i =~ "pull-secret" ]]; then
        oc get secret -n openshift-config | grep pull
    fi

    if [[ $i =~ "catalog" ]]; then
        oc get catalogsource -n openshift-marketplace | grep ibm
        sleep 10s
    fi

    if [[ $i =~ "operatorgroup" ]]; then
        oc get operatorgroup
    fi

    if [[ $i =~ "configmap" ]]; then
        oc get configmap common-service-maps -n kube-public
    fi

    if [[ $i =~ "crd" ]]; then
         oc get customresourcedefinition | grep commonservices.operator.ibm.com
    fi

    if [[ $i =~ "commonservice" ]]; then
        oc get commonservice
    fi

    if [[ $i =~ "singleton-subscriptions" ]]; then
        timeout 20 oc get pod -n $ns -w
    fi

    if [[ $i =~ "cert-manager" ]]; then
        timeout 20 oc get certificates
    fi

    if [[ $i =~ "subscriptions" ]]; then
        timeout 20 oc get pod -n $ns -w
        podname=$(oc get pod -n openshift-operator-lifecycle-manager  | grep catalog-operator- | awk '{print $1}')
        logs_available=$(oc logs -n openshift-operator-lifecycle-manager $podname | grep "unable to get installplan from cache" | wc -l)
        if [ $logs_available -gt 0 ]; then
            subname=$(oc get Subscription -n $ns | grep ibm-common-service-operator- | awk '{print $1}')
            oc patch Subscription $subname -n $ns -p '{"metadata":{"olm.generated-by":""}}' --type=merge


            while true; do
                printf "\x1B[1mDid you deleted the metadata.annotations.olm.generated-by from Subscription $subname  (Yes/No): \x1B[0m"
                read -rp "" ans
                case "$ans" in
                "y"|"Y"|"yes"|"Yes"|"YES")
                    break
                    ;;
                "n"|"N"|"no"|"No"|"NO")
                    info "Please delete the metadata.annotations.olm.generated-by from Subscription $subname "
                    ;;
                *)
                    echo -e "Answer must be \"Yes\" or \"No\"\n"
                    ;;
                esac
            done


        fi
    fi

    if [[ $i =~ "nss" ]]; then
        timeout 20 oc get pod -n $ns -w
    fi
    
    if [[ $i =~ "licensing" ]]; then
        oc get configmap | grep licensing
    fi

    if [[ $i =~ "licensing" ]]; then
        oc get operandrequest
    fi

    if [[ $i =~ "cs-db" ]]; then
        velero restore logs restore-cs-db-data
    fi
    
    if [[ $i =~ "zen" ]]; then
        chk_zen
    fi

    if [[ $i =~ "zen5-data" ]]; then
         velero restore logs restore-zen5-data
    fi
    shouldicontinue $i
    echo -e "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ Restore - end of resource $i @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n"
done
