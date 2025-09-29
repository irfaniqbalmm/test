#!/bin/bash

CUR_DIR=$(
  cd $(dirname $0)
  pwd
)

function show_help {
  echo -e "\nUsage: CreateUser.sh -u dbauser -p Passwd1\n"
  echo "Options:"
  echo "  -u  Name of the user you want?"
  echo "  -p  Password for that user?"
}

while getopts "h?u:p:" opt; do
  case "$opt" in
  h | \?)
    show_help
    exit 0
    ;;
  u)
    USER=$OPTARG
    ;;
  p)
    PASSWORD=$OPTARG
    ;;
  :)
    echo "Invalid option: -$OPTARG requires an argument"
    show_help
    exit 1
    ;;
  esac
done

yum install -y httpd-tools

mkdir -p ./htpasswd

touch ./htpasswd/users.htpasswd

htpasswd -c -B -b ./htpasswd/users.htpasswd "${USER}" "${PASSWORD}"

oc create secret generic htpass-secret --from-file=htpasswd=./htpasswd/users.htpasswd -n openshift-config
oc apply -f ./htpasswd.yaml
