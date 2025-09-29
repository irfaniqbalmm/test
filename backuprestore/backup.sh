#!/bin/bash

 NS=cp

#scaling down the pods
oc scale deploy ibm-cp4a-operator --replicas=0
oc scale deploy ibm-pfs-operator  --replicas=0
oc scale deploy ibm-content-operator  --replicas=0
for i in `oc get deploy -o name |grep content`; do oc scale $i --replicas=0; done
for i in `oc get sts -o name |grep content`; do oc scale $i --replicas=0; done


#Take backup of secrets
echo "Taking backup of content-cpe-oidc-secret"
oc get secret  content-cpe-oidc-secret -o yaml | yq eval 'del(.metadata.annotations, .metadata.creationTimestamp, .metadata.ownerReferences, .metadata.resourceVersion, .metadata.uid)' -    >  content-cpe-oidc-secret.yaml
echo "Taking backup of admin-user-details"
oc get secret admin-user-details -o yaml | yq eval 'del(.metadata.annotations, .metadata.creationTimestamp, .metadata.ownerReferences, .metadata.resourceVersion, .metadata.uid)' -    >  admin-user-details.yaml
echo "Taking backup of ibm-entitlement-key"
oc get secret ibm-entitlement-key -o yaml | yq eval 'del(.metadata.annotations, .metadata.creationTimestamp, .metadata.ownerReferences, .metadata.resourceVersion, .metadata.uid)' -    >  ibm-entitlement-key.yaml
echo "Taking backup of ldap-bind-secret"
oc get secret ldap-bind-secret -o yaml | yq eval 'del(.metadata.annotations, .metadata.creationTimestamp, .metadata.ownerReferences, .metadata.resourceVersion, .metadata.uid)' -    >  ldap-bind-secret.yaml
echo "Taking backup of ibm-cp4ba-ldap-ssl-secret"
oc get secret ibm-cp4ba-ldap-ssl-secret -o yaml | yq eval 'del(.metadata.annotations, .metadata.creationTimestamp, .metadata.ownerReferences, .metadata.resourceVersion, .metadata.uid)' -    >  ibm-cp4ba-ldap-ssl-secret.yaml
echo "Taking backup of ibm-cp4ba-db-ssl-secret-for-db"
oc get secret ibm-cp4ba-db-ssl-secret-for-db -o yaml | yq eval 'del(.metadata.annotations, .metadata.creationTimestamp, .metadata.ownerReferences, .metadata.resourceVersion, .metadata.uid)' -    >   ibm-cp4ba-db-ssl-secret-for-db.yaml
echo "Taking backup of content-rr-admin-secret"
oc get secret content-rr-admin-secret -o yaml | yq eval 'del(.metadata.annotations, .metadata.creationTimestamp, .metadata.ownerReferences, .metadata.resourceVersion, .metadata.uid)' -    >  content-rr-admin-secret.yaml
echo "Taking backup of ibm-ban-secret"
oc get secret ibm-ban-secret -o yaml | yq eval 'del(.metadata.annotations, .metadata.creationTimestamp, .metadata.ownerReferences, .metadata.resourceVersion, .metadata.uid)' -    >  ibm-ban-secret.yaml
echo "Taking backup of ibm-fncm-secret "
oc get secret ibm-fncm-secret -o yaml | yq eval 'del(.metadata.annotations, .metadata.creationTimestamp, .metadata.ownerReferences, .metadata.resourceVersion, .metadata.uid)' -    >  ibm-fncm-secret.yaml


#Take backup of the pvc
pvcbackup() { 
oc get pvc -n $NS --no-headers=true | while read each
do
    pvc=`echo $each | awk '{ print $1 }'`
    echo "---" >> pvc.yaml    
    kubectl get pvc $pvc -o yaml \
      | yq eval 'del(.status, .metadata.finalizers, .metadata.resourceVersion, .metadata.uid, .metadata.annotations, .metadata.creationTimestamp, .metadata.selfLink, .metadata.managedFields, .metadata.ownerReferences, .spec.volumeMode, .spec.volumeName)' -  >> pvc.yaml
    
done
}
echo "Taking backup of pvc definitions"
pvcbackup  



#PV backup
SOURCE_DIR=/data
BACKUP_DIR=/opt/Cp4ba-Automation/backuprestore/backup 
 
pvbackup() { 
    oc get pvc -n $NS --no-headers=true | while read each 
    do 
        pvc=`echo $each | awk '{ print $1 }'` 
    	pv=`echo $each | awk '{ print $3 }'` 
    	 
        if [  -d "$SOURCE_DIR/$NS-$pvc-$pv" ] 
    	then 
            echo "copying pv $pv " 
    		mkdir -p $BACKUP_DIR/$pvc 
    		cp -r -a $SOURCE_DIR/$NS-$pvc-$pv/.  $BACKUP_DIR/$pvc 
            echo "" 
        else 
            echo "NOT FOUND for $pvc" 
        fi 
    done 
} 
echo "Taking backup of pv data"
pvbackup 


#Run labelling catalogsource
oc label catalogsource bts-operator-v3-35-1 foundationservices.cloudpak.ibm.com=catalog -n cp --overwrite=true
oc label catalogsource ibm-cp4a-operator-catalog foundationservices.cloudpak.ibm.com=catalog -n cp --overwrite=true
oc label catalogsource ibm-cert-manager-catalog foundationservices.cloudpak.ibm.com=catalog -n ibm-cert-manager --overwrite=true
oc label catalogsource ibm-licensing-catalog foundationservices.cloudpak.ibm.com=catalog -n ibm-licensing --overwrite=true
oc label catalogsource cloud-native-postgresql-catalog foundationservices.cloudpak.ibm.com=catalog -n cp --overwrite=true
oc label catalogsource ibm-cs-install-catalog-v4-9-0 foundationservices.cloudpak.ibm.com=catalog -n cp --overwrite=true
oc label catalogsource ibm-cs-opensearch-catalog foundationservices.cloudpak.ibm.com=catalog -n cp --overwrite=true
oc label catalogsource ibm-events-operator-catalog foundationservices.cloudpak.ibm.com=catalog -n cp --overwrite=true
oc label catalogsource ibm-fncm-operator-catalog foundationservices.cloudpak.ibm.com=catalog -n cp --overwrite=true
oc label catalogsource ibm-iam-operator-catalog-4-8-0 foundationservices.cloudpak.ibm.com=catalog -n cp --overwrite=true
oc label catalogsource ibm-opencontent-flink foundationservices.cloudpak.ibm.com=catalog -n cp --overwrite=true
oc label catalogsource ibm-zen-operator-catalog-6-0-4 foundationservices.cloudpak.ibm.com=catalog -n cp --overwrite=true


#Labelling the namespace
oc label namespace cp foundationservices.cloudpak.ibm.com=namespace --overwrite=true
oc label namespace ibm-cert-manager foundationservices.cloudpak.ibm.com=namespace --overwrite=true
oc label namespace ibm-licensing foundationservices.cloudpak.ibm.com=namespace --overwrite=true
oc label namespace cp foundationservices.cloudpak.ibm.com=namespace --overwrite=true


#Labelling operatorgroup
oc label operatorgroup ibm-cp4a-operator-catalog-group foundationservices.cloudpak.ibm.com=operatorgroup --overwrite=true -n cp
oc label operatorgroup ibm-cert-manager-operator foundationservices.cloudpak.ibm.com=operatorgroup --overwrite=true -n ibm-cert-manager
oc label operatorgroup ibm-licensing-operator-app foundationservices.cloudpak.ibm.com=operatorgroup --overwrite=true -n ibm-licensing

#Get the common servive operator name
oc get subscription -n cp | grep ibm-common-service-operator

#Apply the label to the common service operator
oc label subscriptions.operators.coreos.com ibm-common-service-operator-v4.9-ibm-cs-install-catalog-v4-9-0-cp foundationservices.cloudpak.ibm.com=subscription --overwrite=true -n cp

#Label subscription of the cert-manager
oc label subscriptions.operators.coreos.com ibm-cert-manager-operator foundationservices.cloudpak.ibm.com=singleton-subscription --overwrite=true -n ibm-cert-manager

#Label subscription of the license operator
oc label subscriptions.operators.coreos.com ibm-licensing-operator-app foundationservices.cloudpak.ibm.com=singleton-subscription --overwrite=true -n ibm-licensing

#Add a label to the common-service custom resource 
oc label commonservices common-service foundationservices.cloudpak.ibm.com=commonservice --overwrite=true

#Add a label to the commonservices.operator.ibm.com customresourcedefinition (CRD)
oc label customresourcedefinition commonservices.operator.ibm.com foundationservices.cloudpak.ibm.com=crd --overwrite=true

#Add a label to the entitlement secret
oc get secret -A | grep ibm-entitlement-key
oc label secret ibm-entitlement-key foundationservices.cloudpak.ibm.com=entitlementkey --overwrite=true -n cp

#Add a label to the global pull secret
oc label secret pull-secret -n openshift-config foundationservices.cloudpak.ibm.com=pull-secret --overwrite=true

#Add a label to the OperandRequests
oc get operandrequests -A
oc label operandrequests bai-apache-flink-request foundationservices.cloudpak.ibm.com=operand --overwrite=true -n cp
oc label operandrequests cloud-native-postgresql-opreq foundationservices.cloudpak.ibm.com=operand --overwrite=true -n cp
oc label operandrequests iaf-system-common-service foundationservices.cloudpak.ibm.com=operand --overwrite=true -n cp
oc label operandrequests bts foundationservices.cloudpak.ibm.com=operand --overwrite=true -n cp
oc label operandrequests ibm-bts-cnpg-operandrequest foundationservices.cloudpak.ibm.com=operand --overwrite=true -n cp
oc label operandrequests ibm-bts-request  foundationservices.cloudpak.ibm.com=operand --overwrite=true -n cp
oc label operandrequests ibm-iam-request foundationservices.cloudpak.ibm.com=operand --overwrite=true -n cp
oc label operandrequests ibm-iam-service  foundationservices.cloudpak.ibm.com=operand --overwrite=true -n cp
oc label operandrequests opensearch-request  foundationservices.cloudpak.ibm.com=operand --overwrite=true -n cp
oc label operandrequests operandrequest-kafka-iaf-system  foundationservices.cloudpak.ibm.com=operand --overwrite=true -n cp
oc label operandrequests postgresql-operator-request  foundationservices.cloudpak.ibm.com=operand --overwrite=true -n cp
oc label operandrequests zen-ca-operand-request  foundationservices.cloudpak.ibm.com=operand --overwrite=true -n cp


#Label the namespacescope CRD and CR:
oc label namespacescope common-service -n cp foundationservices.cloudpak.ibm.com=nss --overwrite=true
oc label customresourcedefinition namespacescopes.operator.ibm.com  foundationservices.cloudpak.ibm.com=nss --overwrite=true

#Label the namespacescope subscription
oc label subscriptions.operators.coreos.com ibm-namespace-scope-operator -n cp foundationservices.cloudpak.ibm.com=nss --overwrite=true

#Label the namespacescope ConfigMap:  
oc label configmap namespace-scope -n cp foundationservices.cloudpak.ibm.com=nss --overwrite=true

#Label the namespacescope service account
oc label serviceaccount ibm-namespace-scope-operator -n cp foundationservices.cloudpak.ibm.com=nss --overwrite=true

#Label the namespacescope roles across namespaces
#Run the following command to find all roles
oc get role -A | grep nss-managed-role-from
oc label role <role name> -n <namespace where role is present> foundationservices.cloudpak.ibm.com=nss --overwrite=true

oc get rolebinding -A | grep nss-managed-role-from
oc label rolebinding <rolebinding name> -n <namespace where rolebinding is present> foundationservices.cloudpak.ibm.com=nss --overwrite=true


# Backup common-service-db. Update the storage d namespace and apply it
wget https://raw.githubusercontent.com/IBM/ibm-common-service-operator/scripts-adopter/velero/schedule/common-service-db/cs-db-backup-deployment.yaml
wget https://raw.githubusercontent.com/IBM/ibm-common-service-operator/scripts-adopter/velero/schedule/common-service-db/cs-db-backup-pvc.yaml
wget https://raw.githubusercontent.com/IBM/ibm-common-service-operator/scripts-adopter/velero/schedule/common-service-db/cs-db-br-script-cm.yaml
wget https://raw.githubusercontent.com/IBM/ibm-common-service-operator/scripts-adopter/velero/schedule/common-service-db/cs-db-role.yaml
wget https://raw.githubusercontent.com/IBM/ibm-common-service-operator/scripts-adopter/velero/schedule/common-service-db/cs-db-rolebinding.yaml
wget https://raw.githubusercontent.com/IBM/ibm-common-service-operator/scripts-adopter/velero/schedule/common-service-db/cs-db-sa.yaml

#Back up Zen
oc get zenservice -A
oc label zenservice iaf-zen-cpdservice foundationservices.cloudpak.ibm.com=zen --overwrite=true -n cp

# Back up Zen MetastoreDB
 wget https://raw.githubusercontent.com/IBM/ibm-common-service-operator/scripts/velero/schedule/zen5-backup-deployment.yaml
 wget https://raw.githubusercontent.com/IBM/ibm-common-service-operator/scripts/velero/schedule/zen5-backup-pvc.yaml
 wget https://raw.githubusercontent.com/IBM/ibm-common-service-operator/scripts/velero/schedule/zen5-br-scripts-cm.yaml
 wget https://raw.githubusercontent.com/IBM/ibm-common-service-operator/scripts/velero/schedule/zen5-sa.yaml
 wget https://raw.githubusercontent.com/IBM/ibm-common-service-operator/scripts/velero/schedule/zen5-role.yaml
 wget https://raw.githubusercontent.com/IBM/ibm-common-service-operator/scripts/velero/schedule/zen5-rolebinding.yaml