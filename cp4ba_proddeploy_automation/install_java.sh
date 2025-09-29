#!/bin/bash

echo "Checking the Java for validation."
JRE_VERSION=$(curl -s https://public.dhe.ibm.com/ibmdl/export/pub/systems/cloud/runtimes/java/  | grep -o '[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}' | tail -n 1)
        
#installing java for the validaiton purpose
function install_ibm_jre() {
    echo "Installing required java for the validation."
    local JRE_VERSION=""
    local JRE_VERSION_TMP=""
    JRE_VERSION=$(curl -s https://public.dhe.ibm.com/ibmdl/export/pub/systems/cloud/runtimes/java/  | grep -o '[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}' | tail -n 1)
    if [[ -z $JRE_VERSION ]]; then
        fail "Can NOT access official IBM JRE Repository https://public.dhe.ibm.com/ibmdl/export/pub/systems/cloud/runtimes/java, Please install IBM JRE manually."
        exit 1
    else
        JRE_VERSION_TMP=$(echo "$JRE_VERSION" | sed 's/\./-/2')
        local tmp_file="/tmp/ibm-java.tgz"
        local download_url=https://public.dhe.ibm.com/ibmdl/export/pub/systems/cloud/runtimes/java/${JRE_VERSION}/linux/$(uname -m)/ibm-java-jre-${JRE_VERSION_TMP}-linux-$(uname -m).tgz
        echo -n "Downloading $download_url";
        curl -o $tmp_file -f $download_url
    fi

    if [ ! -e $tmp_file ]; then
        fail "Can NOT access official IBM JRE Repository https://public.dhe.ibm.com/ibmdl/export/pub/systems/cloud/runtimes/java, Please install IBM JRE manually."
        exit 1
    fi

    mkdir -p /opt/ibm/java
    tar -xzf $tmp_file --strip-components=1 -C /opt/ibm/java
    #  add keytool to system PATH.
    echo -n "Add keytool to system environment variable PATH..."; sudo -s export PATH="/opt/ibm/java/jre/bin/:$PATH"; export PATH="/opt/ibm/java/jre/bin/:$PATH"; echo "PATH=$PATH:/opt/ibm/java/jre/bin/" >> ~/.bashrc;echo "done."
    info "IBM JRE has been installed and system enviroment variable PATH was configured. Please run command \"source ~/.bashrc\" before running the validate command again. Exiting this script."
    cd /root
    echo "Changed to root directory"
    source .bashrc
    echo "Running the bashrc command"
    exit 0
}

#Checking the java already installed or not. 
which java &>/dev/null
    if [[ $? -ne 0 ]]; then
        echo -e  "\x1B[1;31mUnable to locate java. You must install it to run this script.\x1B[0m" && \
        install_ibm_jre
    else
        java -version &>/dev/null
        if [[ $? -ne 0 ]]; then
            echo -e  "\x1B[1;31mUnable to locate a Java Runtime. You must install JRE to run this script.\x1B[0m" && \
            install_ibm_jre
        else
            echo "Java located. Proceedign with validation..."
        fi
    fi