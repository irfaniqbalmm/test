#!/bin/bash

# ns=cp25pods


# Label catalogsource
nsoperator=cp2500
nsoperad=cp2500pods

# cmdvalue=$(oc get catalogsource -A --no-headers | awk '{print $1, $2}')
# echo "Command o/p $cmdvalue"
# readarray -t items < <(oc get catalogsource -A --no-headers | awk '{print $1, $2}')

# for line in "${items[@]}"; do
#     nss=$(echo "$line" | awk '{print $1}')
#     if [ "$nss" = "$nsoperator" ] || [ "$nss" = "ibm-cert-manager" ] || [ "$nss" = "ibm-licensing" ]; then
#         resource=$(echo "$line" | awk '{print $2}')
#         echo "oc label catalogsource $resource foundationservices.cloudpak.ibm.com=catalog -n $nss --overwrite=true"
#         oc label catalogsource $resource foundationservices.cloudpak.ibm.com=catalog -n $nss --overwrite=true
#     fi
# done


# echo "oc label configmap common-service-maps -n kube-public foundationservices.cloudpak.ibm.com=configmap --overwrite=true"
# oc label configmap common-service-maps -n kube-public foundationservices.cloudpak.ibm.com=configmap --overwrite=true

# echo "oc label configmap common-web-ui-config foundationservices.cloudpak.ibm.com=configmap --overwrite=true -n $nsoperad"
# oc label configmap common-web-ui-config foundationservices.cloudpak.ibm.com=configmap --overwrite=true -n $nsoperad

# echo "oc label namespace ibm-cert-manager foundationservices.cloudpak.ibm.com=namespace --overwrite=true"
# oc label namespace ibm-cert-manager foundationservices.cloudpak.ibm.com=namespace --overwrite=true
# echo "oc label namespace ibm-licensing foundationservices.cloudpak.ibm.com=namespace --overwrite=true"
# oc label namespace ibm-licensing foundationservices.cloudpak.ibm.com=namespace --overwrite=true


#  oc label namespace cp2500 foundationservices.cloudpak.ibm.com=namespace --overwrite=true
#  oc label namespace ibm-cert-manager  foundationservices.cloudpak.ibm.com=namespace --overwrite=true
#  oc label namespace ibm-licensing foundationservices.cloudpak.ibm.com=namespace --overwrite=true
#  oc label namespace $nsoperator foundationservices.cloudpak.ibm.com=namespace --overwrite=true
#  oc label namespace $nsoperad foundationservices.cloudpak.ibm.com=namespace --overwrite=true
#  oc label namespace cs-control foundationservices.cloudpak.ibm.com=namespace --overwrite=true



# cmdvalue=$(oc get operatorgroup -A --no-headers | awk '{print $1, $2}')
# echo "Command o/p $cmdvalue"
# readarray -t items < <(oc get operatorgroup -A --no-headers | awk '{print $1, $2}')

# for line in "${items[@]}"; do
#     nss=$(echo "$line" | awk '{print $1}')
#     if [ "$nss" = "$nsoperator" ] || [ "$nss" = "ibm-cert-manager" ] || [ "$nss" = "ibm-licensing" ]; then
#         resource=$(echo "$line" | awk '{print $2}')
#         echo "oc label operatorgroup $resource foundationservices.cloudpak.ibm.com=operatorgroup --overwrite=true -n $nss"
#         oc label operatorgroup $resource foundationservices.cloudpak.ibm.com=operatorgroup --overwrite=true -n $nss
#     fi
# done




#echo "Add a label to the IBM Common Service Operator subscription, "
# cmdvalue=$(oc get subscription -A | grep ibm-common-service-operator | awk '{print $1, $2}')
# echo "Command o/p $cmdvalue"
# readarray -t items < <(oc get subscription -A | grep ibm-common-service-operator | awk '{print $1, $2}')

# for line in "${items[@]}"; do
#     nss=$(echo "$line" | awk '{print $1}')
#     if [ "$nss" = "$nsoperator" ] || [ "$nss" = "ibm-cert-manager" ] || [ "$nss" = "ibm-licensing" ]; then
#         resource=$(echo "$line" | awk '{print $2}')
#         echo "oc label subscriptions.operators.coreos.com $resource foundationservices.cloudpak.ibm.com=subscription --overwrite=true -n $nss"
#         oc label subscriptions.operators.coreos.com $resource foundationservices.cloudpak.ibm.com=subscription --overwrite=true -n $nss
#     fi
# done

# #echo "Add the label to the IBM Cert Manager Operator subscription:"
# oc label subscriptions.operators.coreos.com ibm-cert-manager-operator foundationservices.cloudpak.ibm.com=singleton-subscription --overwrite=true -n ibm-cert-manager

#echo "Add a label to the IBM Licensing Operator subscription:"
# cmdvalue=$(oc get subscriptions.operators.coreos.com -n ibm-licensing | grep ibm-licensing-operator | awk '{print $1}')
# echo "Command o/p $cmdvalue"
# readarray -t items < <(oc get subscriptions.operators.coreos.com -n ibm-licensing | grep ibm-licensing-operator | awk '{print $1}')

# for line in "${items[@]}"; do
#     resource=$(echo "$line" | awk '{print $1}')
#     echo "oc label subscriptions.operators.coreos.com $resource foundationservices.cloudpak.ibm.com=singleton-subscription --overwrite=true -n ibm-licensing"
#     oc label subscriptions.operators.coreos.com $resource foundationservices.cloudpak.ibm.com=singleton-subscription --overwrite=true -n ibm-licensing
    
# done

#echo "Add a label to the common-service custom resource (CR):"
# oc label commonservices common-service foundationservices.cloudpak.ibm.com=commonservice --overwrite=true -n $nsoperator
# oc label commonservices common-service foundationservices.cloudpak.ibm.com=commonservice --overwrite=true -n $nsoperator


#echo " Add a label to the commonservices.operator.ibm.com customresourcedefinition (CRD):"
# oc label customresourcedefinition commonservices.operator.ibm.com foundationservices.cloudpak.ibm.com=crd --overwrite=true


#echo " Add a label to the entitlement secret, if you have one in your cluster:"
# oc label secret ibm-entitlement-key foundationservices.cloudpak.ibm.com=entitlementkey --overwrite=true -n $nsoperator
# oc label secret ibm-entitlement-key foundationservices.cloudpak.ibm.com=entitlementkey --overwrite=true -n $nsoperad


#echo " Add a label to the global pull secret, if you have one in your cluster:"
# oc label secret pull-secret -n openshift-config foundationservices.cloudpak.ibm.com=pull-secret --overwrite=true


#echo "Add a label to the OperandRequests:"
# echo "########################################## label each operandrequests ##########################################"
# cmdvalue=$(oc get operandrequests -A | awk '{print $1, $2}')
# echo "Command o/p $cmdvalue"
# readarray -t items < <(oc get operandrequests -A --no-headers | awk '{print $1, $2}')
# for line in "${items[@]}"; do
#     nss=$(echo "$line" | awk '{print $1}')
#     resource=$(echo "$line" | awk '{print $2}')
#     echo "oc label operandrequests $resource foundationservices.cloudpak.ibm.com=operand --overwrite=true -n $nss"
#     oc label operandrequests $resource foundationservices.cloudpak.ibm.com=operand --overwrite=true -n $nss
# done

# echo "Label the namespacescope CRD and CR:"
# oc label namespacescope common-service -n $nsoperator foundationservices.cloudpak.ibm.com=nss --overwrite=true
# oc label customresourcedefinition namespacescopes.operator.ibm.com  foundationservices.cloudpak.ibm.com=nss --overwrite=true

# echo "Label the namespacescope subscription:"
# oc label subscriptions.operators.coreos.com ibm-namespace-scope-operator -n $nsoperator foundationservices.cloudpak.ibm.com=nss --overwrite=true

# echo "Label the namespacescope ConfigMap:"
# oc label configmap namespace-scope -n $nsoperator foundationservices.cloudpak.ibm.com=nss --overwrite=true

# echo "Label the namespacescope service account:"
# oc label serviceaccount ibm-namespace-scope-operator -n $nsoperator foundationservices.cloudpak.ibm.com=nss --overwrite=true

#echo "Label the namespacescope roles across namespaces:"
# cmdvalue=$(oc get role -A | grep nss-managed-role-from | awk '{print $1, $2}')
# echo "Command o/p $cmdvalue"
# readarray -t items < <(oc get role -A | grep nss-managed-role-from | awk '{print $1, $2}')
# for line in "${items[@]}"; do
#     ns=$(echo "$line" | awk '{print $1}')
#     role=$(echo "$line" | awk '{print $2}')
#     echo "oc label role $role -n $ns foundationservices.cloudpak.ibm.com=nss --overwrite=true"
#     oc label role $role -n $ns foundationservices.cloudpak.ibm.com=nss --overwrite=true
# done

# echo "Label the namespacescope role bindings across namespaces:"
# cmdvalue=$(oc get rolebinding -A | grep nss-managed-role-from | awk '{print $1, $2}')
# echo "Command o/p $cmdvalue"
# readarray -t items < <(oc get rolebinding -A | grep nss-managed-role-from | awk '{print $1, $2}')
# for line in "${items[@]}"; do
#     ns=$(echo "$line" | awk '{print $1}')
#     role=$(echo "$line" | awk '{print $2}')
#     echo "oc label rolebinding $role -n $ns foundationservices.cloudpak.ibm.com=nss --overwrite=true"
#     oc label rolebinding $role -n $ns foundationservices.cloudpak.ibm.com=nss --overwrite=true
# done

# echo "Add the foundationservices.cloudpak.ibm.com=nss label to the following resources:"
# oc label subscriptions.operators.coreos.com ibm-namespace-scope-operator foundationservices.cloudpak.ibm.com=nss -n $nsoperator
# oc label namespacescopes.operator.ibm.com common-service foundationservices.cloudpak.ibm.com=nss -n $nsoperator

# oc label customresourcedefinition namespacescopes.operator.ibm.com foundationservices.cloudpak.ibm.com=nss
# oc label serviceaccount ibm-namespace-scope-operator foundationservices.cloudpak.ibm.com=nss -n $nsoperator
# oc label role nss-managed-role-from-$nsoperator foundationservices.cloudpak.ibm.com=nss -n $nsoperator
# oc label role nss-managed-role-from-$nsoperator foundationservices.cloudpak.ibm.com=nss -n $nsoperad
# oc label rolebinding nss-managed-role-from-$nsoperator foundationservices.cloudpak.ibm.com=nss -n $nsoperator
# oc label rolebinding nss-managed-role-from-$nsoperator foundationservices.cloudpak.ibm.com=nss -n $nsoperad
# oc label configmap namespace-scope foundationservices.cloudpak.ibm.com=nss -n $nsoperator


#Downloading the yaml files from the repo
# echo "Backup common-service-db"
# declare -a arr=("cs-db-backup-pvc" "cs-db-br-script-cm" "cs-db-sa" "cs-db-role" "cs-db-rolebinding" "cs-db-backup-deployment")

# ## now loop through the above array
# for i in "${arr[@]}"
# do
#     echo -e "\n\n@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ Restore - start of resource $i @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"
#     wget_status=$(wget --server-response wget https://raw.githubusercontent.com/IBM/ibm-common-service-operator/scripts-adopter/velero/schedule/common-service-db/$i.yaml 2>&1 | awk '/^  HTTP/{print $2}')
#     echo "Wget status code of the restore-$i : $wget_status" 

#     updatestatus=$(sed -i "s/<cs-db namespace>/$nsoperad/g" ./$i.yaml)
#     sed -i "s/<storage class>/managed-nfs-storage/g" ./$i.yaml
#     echo "File ./$i.yaml updated with $nsoperad"

#     #Applying each yaml file
#     oc_apply=$(oc apply -f $i.yaml)
#     echo $oc_apply
# done

# echo -e "\n\n@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ Back up Zen @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"
# cmdvalue=$(oc get zenservice -A --no-headers | awk '{print $1, $2}')
# echo "Command o/p $cmdvalue"
# readarray -t items < <(oc get zenservice -A --no-headers | awk '{print $1, $2}')
# for line in "${items[@]}"; do
#     ns=$(echo "$line" | awk '{print $1}')
#     name=$(echo "$line" | awk '{print $2}')
#     echo "oc label zenservice $name foundationservices.cloudpak.ibm.com=zen --overwrite=true -n $ns"
#     oc label zenservice $name foundationservices.cloudpak.ibm.com=zen --overwrite=true -n $ns
# done


echo -e "\n\n@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ Back up Zen MetastoreDB @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"
declare -a arr=("zen5-backup-pvc" "zen5-br-scripts-cm" "zen5-sa" "zen5-role" "zen5-rolebinding" "zen5-backup-deployment")

## now loop through the above array
for i in "${arr[@]}"
do
    echo -e "\n\n@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ Restore - start of resource $i @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"
    wget_status=$(wget https://raw.githubusercontent.com/IBM/ibm-common-service-operator/scripts-adopter/velero/schedule/$i.yaml 2>&1 | awk '/^  HTTP/{print $2}')
    echo "Wget status code of the restore-$i : $wget_status" 

    updatestatus=$(sed -i "s/<zenservice namespace>/$nsoperad/g" ./$i.yaml)
    sed -i "s/<zenservice name>/iaf-zen-cpdservice/g" ./$i.yaml
    sed -i "s/<storage class>/managed-nfs-storage/g" ./$i.yaml
    echo "File ./$i.yaml updated with $nsoperad"

    #Applying each yaml file
    oc_apply=$(oc apply -f $i.yaml)
    echo $oc_apply
done
