#!/bin/bash
################################################################################
# Licensed Material - Property of IBM
# 5724-I63, 5724-H88, (C) Copyright IBM Corp. 2018 - All Rights Reserved.
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
#   Script to install software on an Ubuntu AWS image.
#
# NOTES
#   1. This is intended to run as root.  When an AWS instance is instantiated
#      the "user data" content is run as root.
#
# The info() function is used to emit log messages.
# It is assumed that SCRIPT and LOGFILE are set in the caller.
function info {
  local lineno=$1; shift
  local ts=$(date +[%Y/%m/%d-%T])
  echo "$ts $SCRIPT($lineno) $*" | tee -a $LOGFILE
}


# The install-software() function installs software used by the boot-strapping scripts.
# It is assumed LOGFILE is set in the caller.
function install-software {
  # Refresh the repositories
  apt update -y 2>&1 | tee -a $LOGFILE

  # Python
  apt install -y python2.7 python-pip 2>&1 | tee -a $LOGFILE

  python --version | tee -a $LOGFILE

  # Upgrade pip
  pip install --upgrade pip 2>&1 | tee -a $LOGFILE

  # jq - Command line JSON parser
  apt install -y jq 2>&1 | tee -a $LOGFILE

  # AWS CLI
  pip install awscli --upgrade 2>&1 | tee -a $LOGFILE

  aws --version | tee -a $LOGFILE

  # AWS ec2-metadata - Handy shell script used to get instance and ami meta-data
  info $LINENO "Installing ec2-metadata script from http://s3.amazonaws.com/ec2metadata/ec2-metadata"
  wget http://s3.amazonaws.com/ec2metadata/ec2-metadata
  chmod +x ec2-metadata
  mv ec2-metadata /usr/bin
  info $LINENO "ec2-metadata installed"

}

############ "Main" starts here
SCRIPT=${0##*/}

# process the input args
# For keyword-value arguments the arg gets the keyword and
# the case statement assigns the value to a script variable.
# If any "switch" args are added to the command line args,
# then it wouldn't need a shift after processing the switch
# keyword.  The script variable for a switch argument would
# be initialized to "false" or the empty string and if the 
# switch is provided on the command line it would be assigned
# "true".
#
while (( $# > 0 )); do
  arg=$1
  case $arg in
    -h|--help ) usage; exit 0
                  ;;

    --logfile|--logFile ) logfile=$2; shift
                  ;;

    * ) usage; info $LINENO "Unknown option: $arg in command line." 
        exit 2
        ;;
  esac
  # shift to next key-value pair
  shift
done

if [ -n "$logfile" ]; then
  LOGFILE="$logfile"
fi

info $LINENO "BEGIN $SCRIPT"

install-software

info $LINENO "END $SCRIPT"
