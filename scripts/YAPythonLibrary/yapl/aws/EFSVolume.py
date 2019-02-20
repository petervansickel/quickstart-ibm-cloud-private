"""
Created on Feb 12, 2019

@author: Peter Van Sickel
"""

import os
from subprocess import call

from yapl.utilities.Trace import Trace
from yapl.exceptions.Exceptions import MissingArgumentException


TR = Trace(__name__)

"""
  Depending on what EFS example you look at the options to the mount command vary.
  The options used in this method are from this AWS documentation:
  https://docs.aws.amazon.com/efs/latest/ug/wt1-test.html
  Step 3.3 has the mount command template and the options are:
  nfsvers=4.1,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2,noresvport
  
  The following defaults options are also included:
    rw,suid,dev,exec,auto,nouser
"""
DefaultEFSMountOptions = "rw,suid,dev,exec,auto,nouser,nfsvers=4.1,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2,noresvport"


class EFSVolume:
  """
    Simple class to manage an EFS volume.

    NOTE: It is assumed that nfs-utils (RHEL) or nfs-common (Ubuntu) has been
    installed on the nodes were EFS mounts are implemented.
   
    Depending on what EFS example you look at the options to the mount command vary.
    The options used in this method are from this AWS documentation:
    https://docs.aws.amazon.com/efs/latest/ug/wt1-test.html
    Step 3.3 has the mount command template and the options are:
    nfsvers=4.1,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2,noresvport
    
    The following defaults options are also included:
      rw,suid,dev,exec,auto,nouser
    
  """
  
  def __init__(self,efsServer,mountPoint,options=DefaultEFSMountOptions):
    """
      Constructor
      
      NOTE: The EFSMountOptions are very likely what you want.
    """
    self.efsServer = efsServer
    self.mountPoint = mountPoint
    self.options = options
  #endDef
  
  
  def mount(self, options=""):
    """
      Mount this volume on the exported root of the EFS server on its mount point using
      the given options or the instance options.
      
      If the given options are empty then the instance options are used.
      
      NOTE: The default instance mount options are very likely correct.
      Don't mess with the mount options unless you know what you are doing.
    """
    methodName = "mount"
    
    if (options):
      self.options = options
    #endIf
    
    if (not os.path.exists(self.mountPoint)):
      os.makedirs(self.mountPoint)
      TR.info(methodName,"Created directory for EFS mount point: %s" % self.mountPoint)
    elif (not os.path.isdir(self.mountPoint)):
      raise Exception("EFS mount point path: %s exists but is not a directory." % self.mountPoint)
    else:
      TR.info(methodName,"EFS mount point: %s already exists." % self.mountPoint)
    #endIf
    
    retcode = call("mount -t nfs4 -o %s %s:/ %s" % (self.options,self.efsServer,self.mountPoint), shell=True)
    if (retcode != 0):
      raise Exception("Error return code: %s mounting to EFS server: %s with mount point: %s" % (retcode,self.efsServer,self.mountPoint))
    #endIf
    
    TR.info(methodName,"%s mounted on EFS server: %s:/ with options: %s" % (self.mountPoint,self.efsServer,self.options))

  #endDef
  
#endClass


def mountEFSVolumes(volumes, options=""):
  """
    Mount the EFS storage volumes.
    
    volumes is either a singleton instance of EFSVolume or a list of instances
    of EFSVolume.  EFSVolume has everything needed to mount the volume on a
    given mount point.

    NOTE: The default instance mount options are very likely correct.
    Don't mess with the mount options unless you know what you are doing.

  """
  
  if (not volumes):
    raise MissingArgumentException("One or more EFS volumes must be provided.")
  #endIf
  
  if (type(volumes) != type([])):
    volumes = [volumes]
  #endIf

  for volume in volumes:
    volume.mount(options)
  #endFor
#endDef

  
        