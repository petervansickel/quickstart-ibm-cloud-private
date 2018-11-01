
"""
Created on Oct 23, 2018

@author: Peter Van Sickel - pvs@us.ibm.com

NOTES:
  The ICP Knowledge Center has instructions for setting up the Helm CLI
  in the section "Setting up the Helm CLI".  For ICP 3.1.0 the URL for 
  that section is: 
  https://www.ibm.com/support/knowledgecenter/SSBS6K_3.1.0/app_center/create_helm_cli.html
  
  This class emulates those instructions.
  
  We also had as a guide the setup-helm.sh script written by Sanjay Joshi.
  
"""

import requests
import stat
import os
from subprocess import check_call, check_output, CalledProcessError
import shutil
import tarfile

from yapl.utilities.Trace import Trace, Level
from yapl.exceptions.Exceptions import MissingArgumentException


TR = Trace(__name__)

"""
Got this context manager from:
https://stackoverflow.com/questions/431684/how-do-i-change-directory-cd-in-python/13197763#13197763
"""
class cd:
    """Context manager for changing the current working directory"""
    def __init__(self, newPath):
        self.newPath = os.path.expanduser(newPath)
    #endDef

    def __enter__(self):
        self.savedPath = os.getcwd()
        if (TR.isLoggable(Level.FINEST)):
          TR.finest("cd.__enter__","Current working directory: %s changing to: %s" % (self.savedPath, self.newPath))
        #endIf
        os.chdir(self.newPath)
    #endDef

    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)
    #endDef
#endClass


class ConfigureHelm(object):
  """
    Class to configure Helm command line for IBM Cloud Private
    
    The clusterDNSName is the fully qualified domain name used to identify the cluster.
    It is assumed that there is an entry in /etc/hosts that resolves the clusterDNSName.
    Or there is an entry in some DNS that resolves the clusterDNSName.
    
    The clusterDNSName is the FQDN used to access the ICP master node(s).
    
  """


  def __init__(self, clusterDNSName):
    """
      Constructor
    """
    object.__init__(self)
    
    if (not clusterDNSName):
      raise MissingArgumentException("The cluster DNS name to be used to access the ICP master must be provided.")
    #endIf

    self.home = os.path.expanduser('~')
    self.clusterDNSName = clusterDNSName
  #endDef
  
  
  def installHelm(self):
    """
      After the cluster is up and running, install Helm.
            
      ASSUMPTIONS:
        1. ICP is installed and running
        2. An entry in /etc/hosts exists to resolve the clusterDNSName to an IP address
        3. Verifying the SSL connection to the master is irrelevant.  The master may
           be using a self-signed certificate.        
    """
    methodName = 'installHelm'
     
    tgzPath = "/tmp/helm-linux-amd64.tar.gz"
    url = "https://%s:8443/api/cli/helm-linux-amd64.tar.gz" % self.clusterDNSName
    
    if (TR.isLoggable(Level.FINEST)):
      TR.finest(methodName,"Downloading Helm tgz file from: %s to: %s" % (url,tgzPath))
    #endIf
    r = requests.get(url, verify=False, stream=True)
    with open(tgzPath, 'wb') as tgzFile:
      shutil.copyfileobj(r.raw, tgzFile)
    #endWith
 
    if (TR.isLoggable(Level.FINEST)):
      TR.finest(methodName,"Extracting the Helm tgz archive: %s" % tgzPath)
    #endIf
    helmTarFile = tarfile.open(name=tgzPath,mode='r')
    helmTarFile.extractall(path="/tmp")
    helmTarFile.close()
    
    helmSrcPath = "/tmp/linux-amd64/helm"
    helmDestPath = "/usr/local/bin/helm" 
    if (TR.isLoggable(Level.FINEST)):
      TR.finest(methodName,"Moving helm executable from: %s to: %s" % (helmSrcPath,helmDestPath))
    #endIf
    
    shutil.move(helmSrcPath, helmDestPath)
    
    if (TR.isLoggable(Level.FINEST)):
      TR.finest(methodName,"Modifying helm executable mode bits to 755")
    #endIf
    os.chmod(helmDestPath, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
  
  #endDef
  

  def getClusterCACert(self, certFilePath):
    """
      Use openssl to get the CA cert of the cluster to be used by helm for secure connections to Tiller.
      
      The approach is from Sanjay Joshi's script, and can also be found in numerous references on the Internet.
    """
    methodName = 'getClusterCACert'
    
    if (not certFilePath):
      raise MissingArgumentException("The destination file path for the X.509 certificate must be provided.")
    #endIf
    
    try:
      TR.info(methodName, "Invoking: openssl s_client -showcerts -connect %s:8443 < /dev/null 2> /dev/null | openssl x509 -outform PEM > %s" % (self.clusterDNSName,certFilePath))
      #check_call(["openssl", "s_client", "-showcerts", "-connect", "%s:8443" % self.clusterDNSName, "<", "/dev/null", "2>", "/dev/null", "|", "openssl", "x509", "-outform", "PEM", ">", "%s" % certFilePath])
      check_call("openssl s_client -showcerts -connect {0}:8443 < /dev/null 2> /dev/null | openssl x509 -outform PEM > {1}".format(self.clusterDNSName,certFilePath), shell=True)
    except CalledProcessError as e:
      TR.error(methodName,"Exception getting cluster CA cert: %s" % e, e)
      raise e
    #endIf
      
  #endDef
  
  
  def configureHelm(self):
    """
      Configure helm after helm executable has been installed.
      
      Helm is assumed to be installed and in the PATH.

      IMPORTANT: It is critical to set up HELM_HOME within the context of the Python process.
      The HELM_HOME setting done by the helm init command is either not visible in the context
      of the Python process or it is incorrect. If HELM_HOME is not set correctly the repo add
      commands fail.

    """
    methodName = 'configureHelm'
    
    try:
      TR.info(methodName, "Invoking: helm init --client-only")
      output = check_output(["helm", "init", "--client-only"])
      if (output): TR.info(methodName,"helm init output:\n%s" % output.rstrip())
    except CalledProcessError as e:
      if (e.output): TR.info(methodName,"ERROR: helm init output:\n%s" % e.output.rstrip())
      TR.error(methodName,"Exception calling helm init: %s" % e, e)
      raise e
    #endTry

    # Set HELM_HOME to the full path and visible to the Python process context.
    os.environ['HELM_HOME'] = "{home}/.helm".format(home=self.home)
    if (TR.isLoggable(Level.FINEST)):
      TR.finest(methodName,"HELM_HOME=%s" % os.environ.get('HELM_HOME'))
    #endIf
    
    try:
      TR.info(methodName, "Invoking: helm repo add ibm-charts https://raw.githubusercontent.com/IBM/charts/master/repo/stable/")
      output = check_output(["helm", "repo", "add", "ibm-charts", "https://raw.githubusercontent.com/IBM/charts/master/repo/stable/"])
      if (output):
        TR.info(methodName,"helm repo add ibm-charts output:\n%s" % output.rstrip())
      #endIf
    except CalledProcessError as e:
      if (e.output): TR.info(methodName,"ERROR: repo add ibm-charts output:\n%s" % e.output.rstrip())
      TR.error(methodName,"Exception calling repo add ibm-charts: %s" % e, e)
    #endTry
    
    try:
      TR.info(methodName, "Invoking: helm repo add ibmcase-spring https://raw.githubusercontent.com/ibm-cloud-architecture/refarch-cloudnative-spring/master/docs/charts/")
      output = check_output(["helm", "repo", "add", "ibmcase-spring", "https://raw.githubusercontent.com/ibm-cloud-architecture/refarch-cloudnative-spring/master/docs/charts/"])
      if (output):
        TR.info(methodName,"helm repo add ibmcase-spring output:\n%s" % output.rstrip())
      #endIf
    except CalledProcessError as e:
      if (e.output): TR.info(methodName,"ERROR: repo add ibmcase-spring output:\n%s" % e.output.rstrip())
      TR.error(methodName,"Exception calling repo add ibmcase-spring: %s" % e, e)
    #endTry
    
    self.clusterCertPath = os.path.join(self.home,"cluster-ca.crt")
    self.getClusterCACert(self.clusterCertPath)
    
    try:
      TR.info(methodName, "Invoking: helm repo add --ca-file {cacert} --cert-file {home}/.kube/kubecfg.crt --key-file {home}/.kube/kubecfg.key mgmt-charts https://{cluster}:8443/mgmt-repo/charts".format(cacert=self.clusterCertPath,home=self.home,cluster=self.clusterDNSName))
      output = check_output(["helm", "repo", "add", "--ca-file", self.clusterCertPath, "--cert-file", "%s/.kube/kubecfg.crt" % self.home, "--key-file", "%s/.kube/kubecfg.key" % self.home, "mgmt-charts", "https://%s:8443/mgmt-repo/charts" % self.clusterDNSName])
      if (output): TR.info(methodName,"helm repo add mgmt-charts output:\n%s" % output.rstrip())
    except CalledProcessError as e:
      if (e.output): TR.info(methodName,"ERROR: repo add mgmt-charts output:\n%s" % e.output.rstrip())
      TR.error(methodName,"Exception calling repo add mgmt-charts: %s" % e, e)
    #endTry

  #endDef
  
  def installAndConfigureHelm(self):
    """
      Install and configure Helm
    """
    self.installHelm()
    self.configureHelm()
  #endDef
  
#endClass