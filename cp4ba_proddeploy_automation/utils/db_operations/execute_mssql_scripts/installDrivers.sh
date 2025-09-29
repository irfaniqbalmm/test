#!/bin/bash

# Download appropriate package for the OS version
if [ -f /etc/redhat-release ]; then
  if grep -qs "release 7" /etc/redhat-release; then
    curl https://packages.microsoft.com/config/rhel/7/prod.repo | sudo tee /etc/yum.repos.d/mssql-release.repo
  elif grep -qs "release 8" /etc/redhat-release; then
    curl https://packages.microsoft.com/config/rhel/8/prod.repo | sudo tee /etc/yum.repos.d/mssql-release.repo
  elif grep -qs "release 9" /etc/redhat-release; then
    curl https://packages.microsoft.com/config/rhel/9/prod.repo | sudo tee /etc/yum.repos.d/mssql-release.repo
  fi
fi

# Remove conflicting packages
sudo yum remove unixODBC-utf16 unixODBC-utf16-devel

# Install msodbcsql18
sudo ACCEPT_EULA=Y yum install -y msodbcsql18

# Install mssql-tools18 (optional)
sudo ACCEPT_EULA=Y yum install -y mssql-tools18

# Add PATH to ~/.bashrc
echo 'export PATH="$PATH:/opt/mssql-tools18/bin"' >> ~/.bashrc
source ~/.bashrc

# Install unixODBC-devel (optional)
sudo yum install -y unixODBC-devel