#!/bin/sh 

#Checking the number of arguments are 1. Supplying the namespace
if [ "$#" -ne 1 ]
then
  echo "Incorrect number of arguments"
  echo $# arguments
  exit 1
fi

NS=$1 
SOURCE_DIR=/data
BACKUP_DIR=./$NS/
SECRET='secret'
mkdir -p $SECRET

#You can scale down all your environment pods to 0 by running the following commands:
echo "oc scale deploy ibm-cp4a-operator --replicas=0"
oc scale deploy ibm-cp4a-operator --replicas=0
echo "oc scale deploy ibm-pfs-operator  --replicas=0"
oc scale deploy ibm-pfs-operator  --replicas=0
echo "oc scale deploy ibm-content-operator  --replicas=0"
oc scale deploy ibm-content-operator  --replicas=0
for i in `oc get deploy -o name |grep content`; do oc scale $i --replicas=0; done
for i in `oc get sts -o name |grep content `; do oc scale $i --replicas=0; done


#BAcking up the secrets
# oc get secret  content-cpe-oidc-secret -o yaml | /usr/local/bin/yq eval 'del(.metadata.annotations, .metadata.creationTimestamp, .metadata.ownerReferences, .metadata.resourceVersion, .metadata.uid)' ->  ./$SECRET/content-cpe-oidc-secret.yaml
# oc get secret admin-user-details -o yaml | /usr/local/bin/yq eval 'del(.metadata.annotations, .metadata.creationTimestamp, .metadata.ownerReferences, .metadata.resourceVersion, .metadata.uid)' ->  ./$SECRET/admin-user-details.yaml
# oc get secret ibm-entitlement-key -o yaml | /usr/local/bin/yq eval 'del(.metadata.annotations, .metadata.creationTimestamp, .metadata.ownerReferences, .metadata.resourceVersion, .metadata.uid)' ->  ./$SECRET/ibm-entitlement-key.yaml
# oc get secret ldap-bind-secret -o yaml | /usr/local/bin/yq eval 'del(.metadata.annotations, .metadata.creationTimestamp, .metadata.ownerReferences, .metadata.resourceVersion, .metadata.uid)' ->  ./$SECRET/ldap-bind-secret.yaml
# oc get secret ibm-cp4ba-ldap-ssl-secret -o yaml | /usr/local/bin/yq eval 'del(.metadata.annotations, .metadata.creationTimestamp, .metadata.ownerReferences, .metadata.resourceVersion, .metadata.uid)' ->  ./$SECRET/ibm-cp4ba-ldap-ssl-secret.yaml
# oc get secret ibm-cp4ba-db-ssl-secret-for-db -o yaml | /usr/local/bin/yq eval 'del(.metadata.annotations, .metadata.creationTimestamp, .metadata.ownerReferences, .metadata.resourceVersion, .metadata.uid)' ->   ./$SECRET/ibm-cp4ba-db-ssl-secret-for-db.yaml
# oc get secret content-rr-admin-secret -o yaml | /usr/local/bin/yq eval 'del(.metadata.annotations, .metadata.creationTimestamp, .metadata.ownerReferences, .metadata.resourceVersion, .metadata.uid)' ->  ./$SECRET/content-rr-admin-secret.yaml
# oc get secret ibm-ban-secret -o yaml | /usr/local/bin/yq eval 'del(.metadata.annotations, .metadata.creationTimestamp, .metadata.ownerReferences, .metadata.resourceVersion, .metadata.uid)' ->  ./$SECRET/ibm-ban-secret.yaml
# oc get secret ibm-fncm-secret -o yaml | /usr/local/bin/yq eval 'del(.metadata.annotations, .metadata.creationTimestamp, .metadata.ownerReferences, .metadata.resourceVersion, .metadata.uid)' ->  ./$SECRET/ibm-fncm-secret.yaml

declare -a secretarr=("content-cpe-oidc-secret" "admin-user-details" "ibm-entitlement-key" "ldap-bind-secret" "ibm-cp4ba-ldap-ssl-secret" "content-rr-admin-secret" "ibm-adp-secret" "ibm-ban-secret" "ibm-fncm-secret" "ibm-icc-secret" "ibm-iccsap-secret" "ibm-ier-secret")
## now loop through the above array
for secrets in "${secretarr[@]}"
do
    echo -e "\n\n@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ Backingup the secret $secrets @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"
    oc get secret $secrets -o yaml | /usr/local/bin/yq eval 'del(.metadata.annotations, .metadata.creationTimestamp, .metadata.ownerReferences, .metadata.resourceVersion, .metadata.uid)' ->  ./$SECRET/$secrets.yaml
done

#BACK UP YOUR PVC DEFINITIONS AND PV DEFINITIONS BASED ON YOUR TYPE OF PROVISIONING:
pvcbackup() { 
oc get pvc -n $NS --no-headers=true | while read each
do
    pvc=`echo $each | awk '{ print $1 }'`
    echo "---" >> pvc.yaml    
    kubectl get pvc $pvc -o yaml \
      | /usr/local/bin/yq eval 'del(.status, .metadata.finalizers, .metadata.resourceVersion, .metadata.uid, .metadata.annotations, .metadata.creationTimestamp, .metadata.selfLink, .metadata.managedFields, .metadata.ownerReferences, .spec.volumeMode, .spec.volumeName)' -  >> pvc.yaml
    
done
} 
pvcbackup  



#BACKUP THE PV
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
 
pvbackup


#Scaling up the environment pods .
for i in `oc get deploy -o name |grep content`; do echo "  start $i" ; oc scale $i --replicas=1; done
for i in `oc get sts -o name |grep content`; do echo "  start $i" ; oc scale $i --replicas=1; done
echo "  start operators ..."
oc scale deploy ibm-cp4a-operator --replicas=1
oc scale deploy ibm-pfs-operator  --replicas=1
oc scale deploy ibm-content-operator  --replicas=1
