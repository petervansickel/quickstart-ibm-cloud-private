#!/bin/bash
################################################################################
#
# Licensed Material - Property of IBM
# 5724-I63, 5724-H88, (C) Copyright IBM Corp. 2014 - All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication or disclosure
# restricted by GSA ADP Schedule Contract with IBM Corp.
#
# DISCLAIMER:
# The following source code is sample code created by IBM Corporation.
# This sample code is provided to you solely for the purpose of assisting you
# in the  use of  the product. The code is provided 'AS IS', without warranty or
# condition of any kind. IBM shall not be liable for any damages arising out of
# your use of the sample code, even if IBM has been advised of the possibility
# of such damages.
################################################################################
#
# DESCRIPTION
#   Script to bootstrap an Ubuntu instance on AWS cloud.
#
#   Input parameters are defined in the "Global Variables" section below.
#   For purposes of "boot strapping" an AWS instance, the only input needed
#   is the URL for the git repo.
#
#   Once the git repo is pulled in, additional configuration files for
#   the various scripts that get run are assumed to be defined in the
#   git repo itself.
#
#   The approach is going to be to use JSON configuration files and process
#   the JSON with jq, or Python.
#
# INPUTS
#   1. GITREPO - Provide an env var below in the Global Variables section
#      with a URL to the git repository that is to be cloned to the instance.
#      Scripts are then run from that repository to further customize the
#      instance.
#
# NOTES
#   A separate bootstap script is needed for each platform to account for
#   differences among the Linux distributions such as apt vs yum for installing
#   software.  A decision was made to have a separate script for each Linux
#   flavor rather than automatically determine the Linux and branching accordingly.
#   We want to keep this bootstrap script as simple as possible.
#
#   The "user data" facility to associate a script with an AWS instance that
#   runs at deployment has no direct way to provide input parameters to the
#   script.  It looks like the intent of user data is to provide a mechanism
#   to provide a string of input parameters in whatever format.  The script 
#   itself intended to be part of the instance image.
#   However, it is unclear how to kick off a script except through user
#   data.  This bootstrapping script holds its own input parameters and
#   enough logic to install git and pull in a git repository that is
#   then used to further customize the instance.  
#
#   TODO: Further investigation may reveal a more elegant solution to the 
#   bootstrapping scenario.
#
#   So far, we are going down the path of instance customization at deployment
#   time.  We may find that lengthens the deployment time to the point where
#   we may switch over to more customization of the image used as the starting
#   point.
#
################################################################################
#
# The info() function is used to emit log messages.
# It is assumed that SCRIPT and LOGFILE are set in the caller.
#
function info {
  local lineno=$1; shift
  local ts=$(date +[%Y/%m/%d-%T])
  echo "$ts $SCRIPT($lineno) $*" | tee -a $LOGFILE
}

# The install-software() function installs the minimum software needed to
# bootstrap the instance.
# It is assumed LOGFILE is set by the caller.
#
function install-software {
  # Refresh the repositories
  apt update -y 2>&1 | tee -a $LOGFILE
  # install git
  apt install -y git-core 2>&1 | tee -a $LOGFILE

}

################################################################################

##### Begin Global Variables
# Bootstrap needs to run as root (at least for now)
MYHOME=/root

# Provide git repo host, user, repo path
# See below to paste SSH private key for git repo access
# And known_hosts entry for the git repo host.
GITREPO_HOST=github.ibm.com
GITREPO_USER=pvs
GITREPO_PATH=aws-icp-quickstart

# Defining the OS to use for branching in the git repo directories
export OS=ubuntu

###### End Global Variables

############ "Main" starts here
SCRIPT=${0##*/}
# Define a common log file for all operations and functions to tee into.
export LOGFILE=$MYHOME/${SCRIPT%.*}.log
cd $MYHOME

info $LINENO "BEGIN $SCRIPT"
info $LINENO "Installing bootstrap software..."
install-software
rc=$?
if [ "$rc" != "0" ]; then
  info $LINENO "ERROR: Installation of bootstrap software failed."
  exit 1
fi
info $LINENO "Installation of bootstrap software completed."

info $LINENO "Configuring github access key to ~/.ssh/id_rsa_github"
# Paste a base64 encoded private key configured to access the target 
# git repository using ssh.
cat << EOF > ~/.ssh/id_rsa_github
-----BEGIN RSA PRIVATE KEY-----
-----END RSA PRIVATE KEY-----
EOF

# Make sure the permissions on the private key are read-only for owner.
# ssh throws an error if file permissions expose a private key. 
chmod 400 ~/.ssh/id_rsa_github

info $LINENO "Adding stanza for github to ~/.ssh/config"
cat << EOF >> ~/.ssh/config
host $GITREPO_HOST
  HostName $GITREPO_HOST
  IdentityFile ~/.ssh/id_rsa_github
  User git
EOF

info $LINENO "Adding $GITREPO_HOST to ~/.ssh/known_hosts"
cat << EOF >> ~/.ssh/known_hosts
# GITHUB KNOWN HOST ENTRY GOES HERE
EOF

# GITREPO is defined in the bootstrap global variables.
GITREPO="git@${GITREPO_HOST}:${GITREPO_USER}/${GITREPO_PATH}"
info $LINENO "Cloning git repository: $GITREPO ..."
git clone "$GITREPO" 2>&1 | tee -a $LOGFILE
rc=$?
if [ "$rc" != "0" ]; then
  info $LINENO "ERROR: Failed to clone git repository: $GITREPO"
  exit 2
else
  info $LINENO "Git repository cloned: $GITREPO"
fi

cd aws-icp-quickstart/aws-icp-bootstrap/scripts/$OS

info $LINENO "Installing additional software..."
./install-software.sh
info $LINENO "Additional software installation completed."

cd "$MYHOME"

info $LINENO "END $SCRIPT"