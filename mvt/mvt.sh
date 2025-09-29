#!/bin/bash
#-------- Get Operator container versions -------------------------
echo "Getting version info for pod:" $(oc get pods | grep ibm-cp4a-operator | head -1 | awk '{print $1}')
oc exec -it $(oc get pods | grep ibm-cp4a-operator | head -1 | awk '{print $1}') -- bash -c "sleep 3; cat /opt/ibm/version.txt"
echo "---------------------------------------------------------------------------"
echo
#-------- Get FNCM container versions -------------------------
for pod in cpe css graphql navigator cmis es-deploy tm-deploy bastudio iccsap-deploy ier-deploy
do echo "Getting version info for pod:" $(oc get pods | grep -v Completed | grep $pod | head -1 | awk '{print $1}')
oc exec -it $(oc get pods | grep -v Completed | grep $pod | head -1 | awk '{print $1}') -- bash -c "sleep 3; cat /opt/ibm/version.txt"
echo "JAVA VERSION"
oc exec -it $(oc get pods | grep -v Completed | grep $pod | head -1 | awk '{print $1}') -- bash -c "sleep 3; java -version 2>&1 | head -n 1 | cut -d'\"' -f2"
echo "LIBERTY VERSION"
oc exec -it $(oc get pods | grep -v Completed | grep $pod | head -1 | awk '{print $1}') -- bash -c "sleep 3; /opt/ibm/wlp/bin/productInfo version"
echo "---------------------------------------------------------------------------"
echo
done

# -------- Get PVC versions -------------------------
for pvc in $(oc get pvc --no-headers | awk '{print $1}')
do echo "Getting release label info for pvc:" $pvc
echo "Release Version:" $(oc get pvc $pvc -o jsonpath='{.metadata.labels.release}')
echo  "---------------------------------------------------------------------------"
done
