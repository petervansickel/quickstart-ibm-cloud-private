#!/bin/bash
################################################################################
#
# DISCLAIMER:
# The following source code is sample code created by IBM Corporation.
# This sample code is provided to you solely for the purpose of assisting you
# in the  use of  the product. The code is provided 'AS IS', without warranty or
# condition of any kind. IBM shall not be liable for any damages arising out of
# your use of the sample code, even if IBM has been advised of the possibility
# of such damages.
#
################################################################################
#
# DESCRIPTION:
# Script to use AMI and instance tags for environment variables.
#
# This script came from: https://github.com/12moons/ec2-tags-env
#
# PRE-REQ's:
#   1. Python, pip - needed to install AWS CLI
#   2. AWS CLI
#   3. jq  - command line JSON parser
#
# NOTES:
#  The AWS CLI will not run correctly unless it has been configured
#  with a region and maybe the various secrets and a user.
#  TODO - Investigate what it takes to make this run in a deployed instance
#         as root.
#
# ASSUMPTIONS:
#   1. The caller has exported LOGFILE, a fully qualified path to a log file.
#
################################################################################
# The info() function is used to emit log messages.
# It is assumed that SCRIPT and LOGFILE are set in the caller.
#
function info {
  local lineno=$1; shift
  local ts=$(date +[%Y/%m/%d-%T])
  echo "$ts $SCRIPT($lineno) $*" | tee -a $LOGFILE
}

get_instance_tags () {
    local instance_id=$(/usr/bin/curl --silent http://169.254.169.254/latest/meta-data/instance-id)
    echo $(/usr/local/bin/aws ec2 describe-tags --filters "Name=resource-id,Values=$instance_id")
}

get_ami_tags () {
    local ami_id=$(/usr/bin/curl --silent http://169.254.169.254/latest/meta-data/ami-id)
    echo $(/usr/local/bin/aws ec2 describe-tags --filters "Name=resource-id,Values=$ami_id")
}

tags_to_env () {
    local tags=$1
    local key
    local value

    for key in $(echo $tags | /usr/bin/jq -r ".[][].Key"); do
        value=$(echo $tags | /usr/bin/jq -r ".[][] | select(.Key==\"$key\") | .Value")
        key=$(echo $key | /usr/bin/tr '-' '_' | /usr/bin/tr '[:lower:]' '[:upper:]')
        export $key="$value"
    done
}

function ec2-tags2env {

  local ami_tags=$(get_ami_tags)
  local instance_tags=$(get_instance_tags)

  tags_to_env "$ami_tags"
  tags_to_env "$instance_tags"

}


############## MAIN starts here
SCRIPT=${0##*/}
info $LINENO "BEGIN $SCRIPT"

ec2-tags2env

info $LINENO "END $SCRIPT"
