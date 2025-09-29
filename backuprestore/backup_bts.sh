#!/bin/bash

echo "create secret generic s3-credentials"
kubectl create secret generic s3-credentials --from-literal=ACCESS_KEY_ID=<access key here> --from-literal=ACCESS_SECRET_KEY=<secret key here>


#edit the bts cr and add the following
echo "edit the bts cr and add the following"
spec:
  backup:
    barmanObjectStore:
      destinationPath: s3://<s3-bucket-name>/
      s3Credentials:
        accessKeyId:
          key: ACCESS_KEY_ID
          name: s3-credentials
        secretAccessKey:
          key: ACCESS_SECRET_KEY
          name: s3-credentials

#Get the app-user secret
echo "Get the app-user secret"
oc get cluster

oc get secret ibm-bts-cnpg-cp4ba-bts-app -o yaml >postgres-app-credential.yaml

#Create a Backup or ScheduledBackup CR for on-demand or scheduled backups
echo "Create a Backup or ScheduledBackup CR for on-demand or scheduled backups"
apiVersion: postgresql.k8s.enterprisedb.io/v1
kind: Backup
metadata:
  name: ibm-bts-cnpg-cp4ba-bts-backup
spec:
  cluster:
    name: ibm-bts-cnpg-cp4ba-bts

#applying the backup schedule
echo "applying the backup schedule"
oc get backup ibm-bts-cnpg-cp4ba-bts-backup -o yaml