#!/usr/bin/env bash

IP=$(hostname -I | awk '{print $1}')

CUR_DIR=$(
  cd $(dirname $0)
  pwd
)

function show_help {
  echo -e "\nUsage: CreateStorageClass.sh \n"
  echo "Options:"
  echo "  -h  Show help"
}

while getopts "h?" opt; do
  case "$opt" in
  h | \?)
    show_help
    exit 0
    ;;
  :)
    echo "Invalid option: -$OPTARG requires an argument"
    show_help
    exit 1
    ;;
  esac
done

# Setup NFS Storage Class
echo "Creating Project managed-nfs-storage for Dynamic Storage Configuration"
oc new-project managed-nfs-storage
sleep 30s
mkdir -p /data

if ! grep -q "/data \*(rw,sync,no_wdelay,no_root_squash,insecure)" /etc/exports; then
  echo "/data *(rw,sync,no_wdelay,no_root_squash,insecure)" >>/etc/exports
  systemctl restart nfs-server
fi

cp ./managed-nfs-cr.yaml ./managed-nfs-cr-tmp.yaml
sed -i "s/<hostname>/$IP/g" ./managed-nfs-cr-tmp.yaml

oc apply -f "${CUR_DIR}"/managed-nfs-role.yaml -n managed-nfs-storage
oc adm policy add-scc-to-user hostmount-anyuid system:serviceaccount:managed-nfs-storage:nfs-client-provisioner

oc apply -f "${CUR_DIR}"/managed-nfs-crd.yaml -n managed-nfs-storage
oc apply -f "${CUR_DIR}"/managed-nfs-cr-tmp.yaml -n managed-nfs-storage

#delete temp file
rm "${CUR_DIR}"/managed-nfs-cr-tmp.yaml
