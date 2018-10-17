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

"""
Created on Oct 8, 2018

@author: Peter Van Sickel pvs@us.ibm.com
"""

from subprocess import call
import boto3
from yapl.utilities.Trace import Trace, Level
from yapl.exceptions.Exceptions import MissingArgumentException
from yapl.exceptions.Exceptions import InvalidParameterException


TR = Trace(__name__)

"""
  The StackParameters are imported from the root CloudFormation stack in the _init() 
  method below.
"""
StackParameters = {}
StackParameterNames = []

TemplateKeywordMappings = { 
                            'TargetNodes':  'TARGET_NODES',
                            'MountSource':  'MOUNT_SOURCE',
                            'MountPoint':   'MOUNT_POINT',
                            'MountOptions': 'MOUNT_OPTIONS'
                          }

ParameterNames = TemplateKeywordMappings.keys()

DefaultParameterValues = {
                            'TargetNodes': 'worker',
                            'MountOptions': 'rw,suid,dev,exec,auto,nouser,nfsvers=4.1,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2,noresvport',
                         }

EFSVariableParameterMappings = {
                                 'ApplicationStorageMountPoint': 'MountPoint',
                                 'EFSDNSName':                   'MountSource'
                               }

EFSVariableParameterNames = EFSVariableParameterMappings.keys()

class ConfigureEFS(object):
  """
    Configure ICP worker nodes to use EFS dynamic provisioner
  """


  def __init__(self, stackId=None, **restArgs):
    """
      Constructor
      
      The stackId input parameter is expected to be a AWS stack resource ID.
      The stackId is used to get the stack parameters among which is:
         EFSDNSName
         ApplicationStorageMountPoint
      
      The restArgs are keyword arguments that include the following:
        playbookPath       - the path to the playbook to use to configure EFS
        varFilePath        - the path to use for the Ansible playbook input variables file
        varTemplatePath    - the path to the EFS configuration variable template
    """
    object.__init__(self)
    
    if (not stackId):
      raise MissingArgumentException("The CloudFormation boot stack ID (stackId) must be provided.")
    #endIf
    
    self.stackId = stackId
    self.cfnResource = boto3.resource('cloudformation')
    self.varFilePath = "efs"
    self._init(stackId, **restArgs)
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


  def _init(self, stackId, **restArgs):
    """
      Instance initialization constructor helper.
      
      The stackIds input parameter is expected to be a list of AWS stack resource IDs.
      The first stack ID in the list is assumed to be the root stack.
      
      The restArgs are keyword arguments that include the following:
        playbookPath       - the path to the playbook to use
        varFilePath        - the path to use for the Ansible playbook input variables file
        varTemplatePath    - the path to the EFS configuration variable template
    """
    global StackParameters, StackParameterNames
    
    playbookPath = restArgs.get('playbookPath')
    if (not playbookPath):
      raise MissingArgumentException("A ploybook path (playbookPath) must be provided.")
    #endIf

    self.playbookPath = playbookPath
        
    varTemplatePath = restArgs.get('varTemplatePath')
    if (not varTemplatePath):
      raise MissingArgumentException("An EFS configuration variable template file path (varTemplatePath) must be provided.")
    #endIf

    self.varTemplatePath = varTemplatePath
    
    varFilePath = restArgs.get('varFilePath')
    if (not varFilePath):
      raise MissingArgumentException("The path to use for the Ansible playbook input variables file (varFilePath) must be provided.")
    #endIf

    self.varFilePath = varFilePath
    
    StackParameters = self.getStackParameters(stackId)
    StackParameterNames = StackParameters.keys()
    
    efsParms = self.getEFSParameters()
    self.efsParameters = self.fillInDefaultValues(**efsParms)
    self.efsParameterNames = self.efsParameters.keys()
  #endDef


  def getStackParameters(self, stackId):
    """
      Return a dictionary with stack parameter name-value pairs from the  
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


  def getEFSParameters(self):
    """
      Return a dictionary with the EFS related parameter values input from the boot stack.
      
      The keys in the result dictionary are mapped to the actual variable name value used
      in the variable template file.
    """
    result = {}
    
    for name in EFSVariableParameterNames:
      varName = EFSVariableParameterMappings.get(name)
      result[varName] = StackParameters.get(name)
    #endFor
    return result
  #endDef
  
  
  def fillInDefaultValues(self, **restArgs):
    """
      Return a dictionary that is a combination of values in restArgs and 
      default parameter values in DefaultParameterValues.
    """
    
    result = {}
    defaultValues = DefaultParameterValues
    
    for parmName in ParameterNames:
      parmValue = restArgs.get(parmName,defaultValues.get(parmName))
      if (parmValue):
        result[parmName] = parmValue
      #endIf
    #endFor

    return result
  #endDef
  
  
  def _checkForParm(self,line,parameterNames):
    """
      Return a tuple (parmName,macroName) if the given line has a substitution macro using 
      a keyword (macroName) for one of the parameter names given in parameterNames  
      Otherwise, return None.  
      
      Returned tuple is of the form (parameter_name,macro_name)
      Helper method for createConfigFile()
    """
    result = (None,None)
    for parmName in parameterNames:
      macroName = TemplateKeywordMappings.get(parmName)
      if (not macroName):
        raise InvalidParameterException("The parameter name: %s was not found in TemplateKeywordMappings hash map." % parmName)
      #endIf
      macro = "${%s}" % macroName
      if (line.find(macro) >= 0):
        result = (parmName,macroName)
        break
      #endIf
    #endFor
    return result
  #endDef
    
  
  def createVarFile(self, varFilePath, templateFilePath):
    """
      Create an Ansible variable file to be used for configuring EFS (NFS) on
      each of the target nodes.
      
      Using the template file, fill in all the variable strings in the template
      using the parameters provided to the stack instance.
      
      The MOUNT_SOURCE gets special treatment.  When it is processed its value
      is initially the DNS name of the EFS server as created in the CloudFormation
      stack. The full mount source needs to include the source mount point which
      for EFS is always the root of the file system.  Hence in the body of the 
      loop that processes the variables the MOUNT_SOURCE value is modified to 
      include the source mount point.
      
      Comment lines in the template file are written immediately to the var file.
      
      NOTE: It is assumed that a line in the configuration template file has at most
      one parameter defined in it.  A parameter is delimited by ${} with the parameter
      name in the {}.
      
      NOTE: It is assumed a given parameter only appears once in the template file. 
      Once a parameter has been found and replaced in a given line in the template
      file, there is no need to check other lines for that same parameter.
    """
    methodName = "createVarFile"
    
    
    # Make a copy of configParameterNames that can be modified in this method.
    parameterNames = list(self.efsParameterNames)
    
    try:
      with open(templateFilePath,'r') as templateFile, open(varFilePath,'w') as varFile:
        for line in templateFile:
          # Need to strip at least the newline character(s)
          line = line.rstrip()
          if (line.startswith('#')):
            varFile.write("%s\n" % line)
          else:
            parmName,macroName = self._checkForParm(line,parameterNames)
            if (not parmName):
              varFile.write("%s\n" % line)
            else:
              parmValue = self.efsParameters[parmName]
              if (macroName == 'MOUNT_SOURCE'):
                parmValue = "%s:/" % parmValue
              #endIf
              macro = "${%s}" % macroName
              if (TR.isLoggable(Level.FINEST)):
                TR.finest(methodName,"LINE: %s\n\tReplacing: %s with: %s" % (line,macro,parmValue))
              #endIf
              newline = line.replace(macro,"%s" % parmValue)
              if (TR.isLoggable(Level.FINEST)):
                TR.finest(methodName,"NEW LINE: %s" % newline)
              #endIf
              varFile.write("%s\n" % newline)
              # No need to keep checking for parmName, once it has been found in a line in the template.
              parameterNames.remove(parmName)
            #endIf
          #endIf
        #endFor
      #endWith 
    except IOError as e:
      TR.error(methodName,"IOError creating configuration variable file: %s from template file: %s" % (varFilePath,templateFilePath), e)
      raise
    #endTry
  #endDef
  
  
  def runAnsiblePlaybook(self, playbook=None, extraVars="efs-config-vars.yaml", inventory="/etc/ansible/hosts"):
    """
      Invoke a shell script to run an Ansible playbook with the given arguments.
      
      NOTE: Work-around because I can't get the Ansible Python libraries figured out on Unbuntu.
    """
    methodName = "runAnsiblePlaybook"
    
    if (not playbook):
      raise MissingArgumentException("The playbook path must be provided.")
    #endIf
    
    try:
      TR.info(methodName,"Executing: ansible-playbook %s, --extra-vars @%s --inventory %s." % (playbook,extraVars,inventory))
      retcode = call(["ansible-playbook", playbook, "--extra-vars", "@%s" % extraVars, "--inventory", inventory ] )
      if (retcode != 0):
        raise Exception("Error calling ansible-playbook. Return code: %s" % retcode)
      else:
        TR.info(methodName,"ansible-playbook: %s completed." % playbook)
      #endIf
    except Exception as e:
      TR.error(methodName,"Error calling ansible-playbook: %s" % e, e)
      raise
    #endTry    
  #endDef

  
  def configureEFS(self):
    """
      Run the playbook to configure EFS on the target nodes.
    """
    self.createVarFile(self.varFilePath,self.varTemplatePath)
    self.runAnsiblePlaybook(playbook=self.playbookPath, extraVars=self.varFilePath)
  #endDef
#endClass