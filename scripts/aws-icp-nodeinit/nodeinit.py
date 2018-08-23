#!/usr/bin/python
###############################################################################
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
###############################################################################

'''
Created on 24 JUN 2018

@author: Peter Van Sickel pvs@us.ibm.com

Description:
  Node initialization script for ICP AWS Quickstart.  
  The ICP cluster nodes don't do much, but they do need to do a bit of work
  to get the cell bootstrapped.  The boot node does most of the heavy lifting.
  The boot node is not a member of the cluster.

History:
  24 JUN 2018 - pvs - Initial creation.

'''

import sys, os.path
from subprocess import call
import boto3
from botocore.exceptions import ClientError
import socket
import time
import docker
from yapl.utilities.Trace import Trace, Level
import yapl.utilities.Utilities as Utilities
from yapl.exceptions.Exceptions import ExitException
from yapl.exceptions.Exceptions import MissingArgumentException
from yapl.exceptions.ICPExceptions import ICPInstallationException


GetParameterSleepTime = 60 # seconds
GetParameterMaxTryCount = 100
HelpFile = "nodeinit.txt"

TR = Trace(__name__)

"""
  The StackParameters are imported from the CloudFormation stack in the _init() 
  method below.
"""
StackParameters = {}
StackParameterNames = []


class NodeInit(object):
  """
    NodeInit class for AWS ICP Quickstart responsible for steps on the cluster nodes
    that are part of the IBM Cloud Private cluster installation/deployment on AWS.
  """

  ArgsSignature = {
                    '--help':       'string',
                    '--stack-name': 'string',
                    '--stackid':    'string',
                    '--role':       'string',
                    '--logfile':    'string',
                    '--loglevel':   'string',
                    '--trace':      'string'
                   }


  def __init__(self):
    """
      Constructor
      
      NOTE: Some instance variable initialization happens in self._init() which is 
      invoked early in main() at some point after _getStackParameters().
    """
    object.__init__(self)

    self.home = os.path.expanduser("~")
    self.logsHome = os.path.join(self.home,"logs")
    self.sshHome = "%s/.ssh" % self.home
    self.fqdn = socket.getfqdn()
    self.rc = 0
    self.ssm = boto3.client('ssm')
    self.s3  = boto3.client('s3')
    self.cfnResource = boto3.resource('cloudformation')    
  #endDef


  def __getattr__(self,attributeName):
    """
      Support for attributes that are defined in the StackParameterNames list
      and with values in the StackParameters dictionary.  
    """
    attributeValue = None
    if (attributeName in StackParameterNames):
      attributeValue = StackParameters.get(attributeName)
    else:
      raise AttributeError("%s is not a StackParameterName" % attributeName)
    #endIf
  
    return attributeValue
  #endDef


  def __setattr__(self,attributeName,attributeValue):
    """
      Support for attributes that are defined in the StackParameterNames list
      and with values in the StackParameters dictionary.
      
      NOTE: The StackParameters are intended to be read-only.  It's not 
      likely they would be set in the Bootstrap instance once they are 
      initialized in _getStackParameters().
    """
    if (attributeName in StackParameterNames):
      StackParameters[attributeName] = attributeValue
    else:
      object.__setattr__(self, attributeName, attributeValue)
    #endIf
  #endDef


  def _init(self, stackId):
    """
      Additional initialization of the NodeInit instance based on stack parameters.
      
      Invoke getStackParameters() gets all the CloudFormation stack parameters imported
      into the StackParmaters dictionary to make them available for use with the NodeInit 
      instance as instance variables via __getattr__().
    """
    methodName = "_init"
    global StackParameters, StackParameterNames
    
    StackParameters = self._getStackParameters(stackId)
    StackParameterNames = StackParameters.keys()
    
    if (TR.isLoggable(Level.FINEST)):
      TR.finest(methodName,"StackParameterNames: %s" % StackParameterNames)
    #endIf
    
    # On the cluster nodes the default timeout is sufficient.
    self.dockerClient = docker.from_env()
            
  #endDef


  def _getStackParameters(self, stackId):
    """
      Return a dictionary with stack parameter name-value pairs for
      stack parameters relevant to the ICP Configuration from the  
      CloudFormation stack with the given stackId.
      
    """
    result = {}
    
    stack = self.cfnResource.Stack(stackId)
    stackParameters = stack.parameters
    for parm in stackParameters:
      parmName = parm['ParameterKey']
      parmValue = parm['ParameterValue']
      result[parmName] = parmValue
    #endFor
    
    return result
  #endDef
  
  
  

  def _getArg(self,synonyms,args,default=None):
    """
      Return the value from the args dictionary that may be specified with any of the
      argument names in the list of synonyms.

      The synonyms argument may be a Jython list of strings or it may be a string representation
      of a list of names with a comma or space separating each name.

      The args is a dictionary with the keyword value pairs that are the arguments
      that may have one of the names in the synonyms list.

      If the args dictionary does not include the option that may be named by any
      of the given synonyms then the given default value is returned.

      NOTE: This method has to be careful to make explicit checks for value being None
      rather than something that is just logically false.  If value gets assigned 0 from
      the get on the args (command line args) dictionary, that appears as false in a
      condition expression.  However 0 may be a legitimate value for an input parameter
      in the args dictionary.  We need to break out of the loop that is checking synonyms
      as well as avoid assigning the default value if 0 is the value provided in the
      args dictionary.
    """
    value = None
    if (type(synonyms) != type([])):
      synonyms = Utilities.splitString(synonyms)
    #endIf

    for name in synonyms:
      value = args.get(name)
      if (value != None):
        break
      #endIf
    #endFor

    if (value == None and default != None):
      value = default
    #endIf

    return value
  #endDef


  def _usage(self):
    """
      Emit usage info to stdout.
      The _usage() method is invoked by the --help option.
    """
    methodName = '_usage'
    if (os.path.exists(HelpFile)):
      Utilities.showFile(HelpFile)
    else:
      TR.info(methodName,"There is no usage information for '%s'" % __name__)
    #endIf
  #endDef


  def _configureTraceAndLogging(self,traceArgs):
    """
      Return a tuple with the trace spec and logFile if trace is set based on given traceArgs.

      traceArgs is a dictionary with the trace configuration specified.
         loglevel|trace <tracespec>
         logfile|logFile <pathname>

      If trace is specified in the trace arguments then set up the trace.
      If a log file is specified, then set up the log file as well.
      If trace is specified and no log file is specified, then the log file is
      set to "trace.log" in the current working directory.
    """
    logFile = self._getArg(['logFile','logfile'], traceArgs)
    if (logFile):
      TR.appendTraceLog(logFile)
    #endIf

    trace = self._getArg(['trace', 'loglevel'],traceArgs)

    if (trace):
      if (not logFile):
        TR.appendTraceLog('trace.log')
      #endDef

      TR.configureTrace(trace)
    #endIf
    return (trace,logFile)
  #endDef  
        
  
  def addAuthorizedKey(self, authorizedKeyEntry):
    """
      Add the given authorizedKeyEntry to  the ~/.ssh/authorized_keys file.
      
      The authorizedKeyEntry includes the SSH private key and the user and IP address
      of the boot node, e.g., root@10.0.0.152
    """
    if (not os.path.exists(self.sshHome)):
      os.makedirs(self.sshHome)
    #endIf
    
    authKeysPath = os.path.join(self.sshHome, 'authorized_keys')
    
    with open(authKeysPath, "a+") as authorized_keys:
      authorized_keys.write("%s\n" % authorizedKeyEntry)
    #endWith
  #endDef
    

  def getSSMParameterValue(self,parameterKey,expectedValue=None):
    """
      Return the value from the given SSM parameter key.
      
      If an expectedValue is provided, then the wait loop for the SSM get_parameter()
      will continue until the expected value is seen or the try count is exceeded.
      
      NOTE: It is possible that the parameter is not  present in the SSM parameter
      cache when this method is invoked.   When hat happens a ParameterNotFound 
      exception is raised by ssm.get_parameter().  Depending on the trace level,
      that  exception is reported in the log, but ignored.
    """
    methodName = "getSSMParameterValue"
    
    parameterValue = None

    tryCount = 1
    gotit = False
    while not gotit and tryCount <= GetParameterMaxTryCount:
      if (expectedValue == None):
        TR.info(methodName,"Try: %d for getting parameter: %s" % (tryCount,parameterKey))
      else:
        TR.info(methodName,"Try: %d for getting parameter: %s with expected value: %s" % (tryCount,parameterKey,expectedValue))
      #endIf
      try: 
        response = self.ssm.get_parameter(Name=parameterKey)
        
        if (not response):
          if (TR.isLoggable(Level.FINEST)):
            TR.finest(methodName, "Failed to get a response for SSM get_parameter(): %s" % parameterKey)
          #endIf
        else:
          if (TR.isLoggable(Level.FINEST)):
            TR.finest(methodName,"Response: %s" % response)
          #endIf
        
          parameter = response.get('Parameter')
          if (not parameter):
            raise Exception("SSM get_parameter() response returned an empty Parameter.")
          #endIf
          
          parameterValue = parameter.get('Value')
          if (expectedValue == None):
            gotit = True
            break
          else:
            if (parameterValue == expectedValue):
              gotit = True
              break
            else:
              if (TR.isLoggable(Level.FINER)):
                TR.finer(methodName,"For key: %s ignoring value: %s waiting on value: %s" % (parameterKey,parameterValue,expectedValue))
              #endIf
            #endIf
          #endIf
        #endIf
      except ClientError as e:
        etext = "%s" % e
        if (etext.find('ParameterNotFound') >= 0):
          if (TR.isLoggable(Level.FINEST)):
            TR.finest(methodName,"Ignoring ParameterNotFound ClientError on ssm.get_parameter() invocation")
          #endIf
        else:
          raise ICPInstallationException("Unexpected ClientError on ssm.get_parameter() invocation: %s" % etext)
        #endIf
      #endTry
      time.sleep(GetParameterSleepTime)
      tryCount += 1
    #endWhile
    
    if (not gotit):
      if (expectedValue == None):
        raise ICPInstallationException("Failed to get parameter: %s " % parameterKey)
      else:
        raise ICPInstallationException("Failed to get parameter: %s with expected value: %s" % (parameterKey,expectedValue))
      #endIf
    #endIf
      
    return parameterValue
  #endDef
 
    
  def getBootNodePublicKey(self):
    """
      Return the authorized key entry for the ~/.ssh/authorized_keys file.
      The returned string is intended to include the RSA public key as well as the root user
      and IP address of the boot node.  The returned string can be added directly to the
      authorized_keys file.
      
      NOTE: It is possible that the a given cluster node may be checking for the authorized
      key from the boot node, before the boot node has published it in its parameter.  When
      that happens a ParameterNotFound exception is raised by ssm.get_parameter().  That 
      exception is reported in the log, but ignored.
    """
    methodName = "getBootNodePublicKey"
    
    authorizedKeyEntry = ""
    parameterKey = "/%s/boot-public-key" % self.stackName
    tryCount = 1
    response = None
    
    while not response and tryCount <= 100:
      time.sleep(GetParameterSleepTime)
      TR.info(methodName,"Try: %d for getting parameter: %s" % (tryCount,parameterKey))
      try: 
        response = self.ssm.get_parameter(Name=parameterKey)
      except ClientError as e:
        etext = "%s" % e
        if (etext.find('ParameterNotFound') >= 0):
          if (TR.isLoggable(Level.FINEST)):
            TR.finest(methodName,"Ignoring ParameterNotFound ClientError on ssm.get_parameter() invocation")
          #endIf
        else:
          raise ICPInstallationException("Unexpected ClientError on ssm.get_parameter() invocation: %s" % etext)
        #endIf
      #endTry
      tryCount += 1
    #endWhile
    
    if (response and TR.isLoggable(Level.FINEST)):
      TR.finest(methodName,"Response: %s" % response)
    #endIf
    
    if (not response):
      TR.warning(methodName, "Failed to get a response for get_parameter: %s" % parameterKey)
    else:
      parameter = response.get('Parameter')
      if (not parameter):
        raise Exception("get_parameter response returned an empty Parameter.")
      #endIf
      authorizedKeyEntry = parameter.get('Value')
    #endIf
    
    return authorizedKeyEntry
  #endDef
  
  
  def _getDockerImage(self,rootName):
    """
      Return a docker image instance for the given rootName if it is available in 
      the local registry.
      
      Helper for installKubectl() and any other method that needs to get an image
      instance from the local docker registry.
    """
    result = None
    
    imageList = self.dockerClient.images.list()

    for image in imageList:
      imageNameTag = image.tags[0]
      if (imageNameTag.find(rootName) >= 0):
        result = image
        break
      #endIf
    #endFor
    return result
  #endDef
  
  
  def installKubectl(self):
    """
      Copy kubectl out of the kubernetes image to /usr/local/bin
      Convenient for troubleshooting.  
      
      If the kubernetes image is not available then this method is a no-op.
    """
    methodName = "installKubectl"
    
    TR.info(methodName,"STARTED install of kubectl to local host /usr/local/bin.")
    kubeImage = self._getDockerImage("kubernetes")
    if (not kubeImage):
      TR.info(methodName,"Kubernetes image is not available in the local docker registry. Kubectl WILL NOT BE INSTALLED.")
    else:
      TR.info(methodName,"Kubernetes image is available in the local docker registry.  Proceeding with the installation of kubectl.")
      if (TR.isLoggable(Level.FINEST)):
        TR.finest(methodName,"Kubernetes image tags: %s" % kubeImage.tags)
      #endIf
      kubeImageName = kubeImage.tags[0]
      self.dockerClient.containers.run(kubeImageName,
                                       network_mode='host',
                                       volumes={"/usr/local/bin": {'bind': '/data', 'mode': 'rw'}}, 
                                       command="cp /kubectl /data"
                                       )
    #endIf
    TR.info(methodName,"COMPLETED install of kubectl to local host /usr/local/bin.")
  #endDef
  
  
  def putSSMParameterValue(self,parameterKey,parameterValue,description=""):
    """
      Put the given parameterValue to the given parameterKey
      
      Wrapper for dealing with CloudFormation SSM parameters.
    """
    methodName = "putSSMParameterValue"
    
    TR.info(methodName,"Putting value: %s to SSM parameter: %s" % (parameterValue,parameterKey))
    self.ssm.put_parameter(Name=parameterKey,
                           Description=description,
                           Value=parameterValue,
                           Type='String',
                           Overwrite=True)
    TR.info(methodName,"Value: %s put to: %s." % (parameterValue,parameterKey))
    
  #endDef

  
  def publishReadiness(self, stackName, fqdn):
    """
      Put a parameter in /stackName/fqdn indicating readiness for ICP installation to proceed.
    """
    methodName = "publishReadiness"
    
    if (not stackName):
      raise MissingArgumentException("The stack name (stackName) must be provided and cannot be empty.")
    #endIf
    
    if (not fqdn):
      raise MissingArgumentException("The FQDN for this node must be provided and cannot be empty.")
    #endIf
    
    parameterKey = "/%s/%s" % (stackName,fqdn)
    
    TR.info(methodName,"Putting READY to SSM parameter: %s" % parameterKey)
    self.ssm.put_parameter(Name=parameterKey,
                           Description="Cluster node: %s is READY" % fqdn,
                           Value="READY",
                           Type='String',
                           Overwrite=True)
    TR.info(methodName,"Node: %s is READY has been published." % fqdn)

  #endDef
  
  
  def loadICPImages(self):
    """
      Load the IBM Cloud Private images from the installation tar archive.
      
      Loading the ICP installation images on each node prior to kicking off the 
      inception install is an expediency that speeds up the installation process 
      dramatically.
      
      The AWS CloudFormation template downlaods the ICP installation tar ball from
      an S3 bucket to /tmp/icp-install-archive.tgz of each cluster node.  It turns 
      out that download is very fast: typically 3 to 4 minutes.
    """
    methodName = "loadICPImages"
        
    TR.info(methodName,"STARTED docker load of ICP installation images.")
    
    retcode = call("tar -zxvf /tmp/icp-install-archive.tgz -O | docker load | tee /root/logs/load-icp-images.log", shell=True)
    if (retcode != 0):
      raise ICPInstallationException("Error calling: 'tar -zxvf /tmp/icp-install-archive.tgz -O | docker load' - Return code: %s" % retcode)
    #endIf
    
    TR.info(methodName,"COMPLETED Docker load of ICP installation images.")
    
  #endDef
  
  
  def exportLogs(self, bucketName, stackName, logsDirectoryPath):
    """
      Export the deployment logs to the given S3 bucket for the given stack.
      
      Each log will be exported using a path with the stackName at the root and the 
      log file name as the next element of the path.
      
      NOTE: Prefer not to use trace in this method as the bootstrap log file has 
      already had the "END" message emitted to it.
    """
    methodName = "exportLogs"
    
    if (not os.path.exists(logsDirectoryPath)):
      if (TR.isLoggable(Level.FINE)):
        TR.fine(methodName, "Logs directory: %s does not exist." % logsDirectoryPath)
      #endIf
    else:
      logFileNames = os.listdir(logsDirectoryPath)
      if (not logFileNames):
        if (TR.isLoggable(Level.FINE)):
          TR.fine(methodName,"No log files in %s" % logsDirectoryPath)
        #endIf
      else:
        for fileName in logFileNames:
          s3Key = "%s/%s/%s/%s" %(stackName,self.role,self.fqdn,fileName)
          bodyPath = os.path.join(logsDirectoryPath,fileName)
          if (TR.isLoggable(Level.FINE)):
            TR.fine(methodName,"Exporting log: %s to S3: %s:%s" % (bodyPath,bucketName,s3Key))
          #endIf
          self.s3.put_object(Bucket=bucketName, Key=s3Key, Body=bodyPath)
        #endFor
      #endIf
    #endIf
  #endDef

  
  def main(self,argv):
    """
      Main does command line argument processing, sets up trace and then kicks off the methods to
      do the work.
    """
    methodName = "main"

    self.rc = 0
    try:
      ####### Start command line processing
      cmdLineArgs = Utilities.getInputArgs(self.ArgsSignature,argv[1:])

      # if trace is set from command line the trace variable holds the trace spec.
      trace, logFile = self._configureTraceAndLogging(cmdLineArgs)

      if (cmdLineArgs.get("help")):
        self._usage()
        raise ExitException("After emitting help, jump to the end of main.")
      #endIf

      beginTime = Utilities.currentTimeMillis()
      TR.info(methodName,"NINIT0101I BEGIN Node initialization AWS ICP Quickstart version @{VERSION}.")

      if (trace):
        TR.info(methodName,"NINIT0102I Tracing with specification: '%s' to log file: '%s'" % (trace,logFile))
      #endIf
      
      stackId = cmdLineArgs.get('stackid')
      if (not stackId):
        raise MissingArgumentException("The stack ID (--stackid) must be provided.")
      #endIf

      self.stackId = stackId
      TR.info(methodName,"Stack ID: %s" % stackId)

      stackName = cmdLineArgs.get('stack-name')
      if (not stackName):
        raise MissingArgumentException("The stack name (--stack-name) must be provided.")
      #endIf
      
      self.stackName = stackName
      TR.info(methodName,"Stack name: %s" % stackName)
      
      role = cmdLineArgs.get('role')
      if (not role):
        raise MissingArgumentException("The role of this node (--role) must be provided.")
      #endIf
      
      self.role = role
      TR.info(methodName,"Node role: %s" % role)
      
      # Additional initialization of the instance.
      self._init(stackId)
      
      # The sleep() is a hack to give bootnode time to do get its act together.
      # PVS: I've run into rare cases where it appears that the the cluster nodes
      # pick up a bad public key.  I think it may be due to accidentally reusing
      # an ssm parameter.  Don't have time to troubleshoot, now.  I'm thinking 
      # if the boot node gets to it first, it will overwrite anything old that 
      # may be there.
      time.sleep(60)
      
      authorizedKeyEntry = self.getBootNodePublicKey()
      self.addAuthorizedKey(authorizedKeyEntry)
      
      self.publishReadiness(self.stackName,self.fqdn)

      # Wait until boot node completes the Docker installation
      self.getSSMParameterValue("/%s/docker-installation" % self.stackName,expectedValue="COMPLETED")
      
      if (Utilities.toBoolean(self.LoadICPImagesLocally)):
        # Expediency for the ICP installation to have each node load the installation images.
        self.loadICPImages()
        self.installKubectl()
      #endIf
      
      self.putSSMParameterValue("/%s/%s" % (self.stackName,self.fqdn),'READY',description="%s is READY" % self.fqdn)
            

    except ExitException:
      pass # ExitException is used as a "goto" end of program after emitting help info

    except Exception, e:
      TR.error(methodName,"Exception: %s" % e, e)
      self.rc = 1
    finally:
      
      try:
        # Copy the deployment logs in logsHome to the S3 bucket for logs.
        self.exportLogs(self.ICPDeploymentLogsBucketName,self.stackName,self.logsHome)
      except Exception, e:
        TR.error(methodName,"Exception: %s" % e, e)
        self.rc = 1
      #endTry

      endTime = Utilities.currentTimeMillis()
      elapsedTime = (endTime - beginTime)/1000
      
      if (self.rc == 0):
        TR.info(methodName,"NINIT0103I END Node initialization AWS ICP Quickstart.  Elapsed time (seconds): %d" % (elapsedTime))
      else:
        TR.info(methodName,"NINIT0104I FAILED END Node initialization AWS ICP Quickstart.  Elapsed time (seconds): %d" % (elapsedTime))
      #endIf
      
    #endTry

    if (TR.traceFile):
      TR.closeTraceLog()
    #endIf

    sys.exit(self.rc)
  #endDef

#endClass

if __name__ == '__main__':
  mainInstance = NodeInit()
  mainInstance.main(sys.argv)
#endIf
