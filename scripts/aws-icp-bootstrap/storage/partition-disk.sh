#!/bin/bash
#
# DESCRIPTION
#   Script to create a partition on the second disk allocated to the VM
#   Borrowing the code for this from here:
#     https://github.com/Xilinx/PYNQ/blob/master/sdbuild/packages/resizefs/resizefs.sh
#   Also found similar code here:
#     https://superuser.com/questions/332252/how-to-create-and-format-a-partition-using-a-bash-script
#
# The info() function is used to emit log messages.
# It is assumed that SCRIPT and LOGFILE are set in the caller.
function info {
  local lineno=$1; shift
  local ts=$(date +[%Y/%m/%d-%T])
  echo "$ts $SCRIPT($lineno) $*" | tee -a $LOGFILE
}

############ "Main" starts here
SCRIPT=${0##*/}

info $LINENO "BEGIN $SCRIPT"


TGTDEV=/dev/xvdb

info $LINENO "Partitioning $TGTDEV"

# to create the partitions programatically (rather than manually)
# we're going to simulate the manual input to fdisk
# The sed script strips off all the comments so that we can
# document what we're doing in-line with the actual commands
# Note that a blank line (commented as "defualt" will send a empty
# line terminated with a newline to take the fdisk default.
sed -e 's/\s*\([\+0-9a-zA-Z]*\).*/\1/' << EOF | fdisk ${TGTDEV} 2>&1 | tee -a fdisk.log
  o # clear the in memory partition table
  n # new partition
  p # primary partition
  1 # partition number 1
    # default - start at beginning of disk
    # default, extend partition to end of disk
  p # print the in-memory partition table
  w # write the partition table
  q # and we're done
EOF


info $LINENO "$(lsblk)"

info $LINENO "END $SCRIPT"
