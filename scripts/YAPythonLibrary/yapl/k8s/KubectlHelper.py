"""
Created on Nov 7, 2018

@author: Peter Van Sickel - pvs@us.ibm.com

DESCRIPTION:
  Module to assist with programmatically executing helm commands in Python.
  
NOTES:
  The implementation originated as a generalized way to run kubectl commands to
  support the installation of applications deployed to an ICP cluster deployed 
  to the AWS cloud.
  
  The implementation has only been tested in a very limited scope.
  
  It is assumed kubectl has been installed and configured to run with a permanent
  token configuration.

"""
import os
import yaml
from yapl.utilities.Trace import Trace
from yapl.exceptions.Exceptions import MissingArgumentException
from yapl.exceptions.Exceptions import InvalidArgumentException

TR = Trace(__name__)


class KubectlHelper(object):
  """
    Helper class to support the execution of kubectl commands targeted at an ICP cluster.
    
    The primary role of the class is to support the createCommand() method given a 
    list of yaml documents.
    
    This class supports the CommandHelper class.
    
  """
  
  def __init__(self):
    """
      Constructor
    """
    object.__init__(self)
  #endDef
  
  
  def createYamlFile(self, filePath, x):
    """
      Dump a yaml representation of the given object (x) to the given filePath. 
    """
    
    if (not filePath):
      raise MissingArgumentException("The file path (filePath) cannot be empty or None.")
    #endIf
    
    if (not x):
      raise MissingArgumentException("The object (x) to be dumped to the file cannot be empty or None.")
    #endIf
    
    destDirPath = os.path.dirname(filePath)
    
    if (not os.path.exists(destDirPath)):
      os.makedirs(destDirPath)
    #endIf
    
    with open(filePath, 'w') as yamlFile:
      yaml.dump(x,yamlFile,default_flow_style=False)
    #endWith
    
    return filePath
  #endDef
  
  
  def processFileOption(self,destDirPath,optionValue,obj):
    """
      Processing for the -f option of a kubectl command.
      
      Helper to createCommands()
    """
    if (not optionValue.endswith(".yaml")):
      fileName = "%s.yaml" % optionValue
    else:
      fileName = optionValue
    #endIf
    
    filePath = os.path.join(destDirPath,fileName)
    self.createYamlFile(filePath,obj)
    return filePath
  #endDef
  
  
  def createCommand(self,cmdDocs,**kwargs):
    """
      Return a command dictionary with a command list and a command string.  
      Either the list or the string can be used with subprocess.call().  
      The command string is useful for emitting trace.
      
      The command dictionary looks like:
      { cmdList: [ ... ], cmdString: "..." }
      
      cmdDocs - a list of 1 or more YAML documents loaded from yaml.load_all()
      by the caller.
      
      kwargs for the KubectlHelper may include the following:
        stagingDirPath - directory path where a yaml file is to be created to be used with the -f option
                         to a kubectl create or apply command 
      
    """
    if (not cmdDocs):
      raise MissingArgumentException("A non-empty list of command documents (cmdDocs) must be provided.")
    #endIf
    
    cmdStr = "kubectl"
    cmdList = [ 'kubectl' ]
    
    cmdDoc = cmdDocs[0]
    
    command = cmdDoc.get('command')
    if (not command):
      raise InvalidArgumentException("The first command document in %s, must have a command attribute." % cmdDocs)
    #endIf
    
    cmdList.append(command)
    cmdStr = "%s %s" % (cmdStr,command)
    
    flags = cmdDoc.get('flags')
    if (flags):
      for flag in flags:
        if (len(flag) > 1):
          # multi-character flags get a double dash
          cmdList.append('--%s' % flag)
          cmdStr = "%s --%s" % (cmdStr,flag)
        else:
          # single character flags get a single dash
          cmdList.append('-%s' % flag)
          cmdStr = "%s -%s" % (cmdStr,flag)
        #endIf          
      #endFor
    #endIf
          
    options = cmdDoc.get('options')
    if (options):
      optionNames = options.keys()
      for optionName in optionNames:
        value = options.get(optionName)
        if (len(optionName) > 1):
          cmdList.append("--%s" % optionName)
          cmdStr = "%s --%s" % (cmdStr,optionName)
        else:
          cmdList.append("-%s" % optionName)
          cmdStr = "%s -%s" % (cmdStr,optionName)
        #endIf
        if (optionName == 'f'):
          # Check that there is a second document in the command file
          # The second document is the yaml that gets dumped to a file for the -f option
          if (len(cmdDocs) < 2):
            raise InvalidArgumentException("Expecting a second document to be used with the -f option in command documents: %s ." % cmdDocs)
          #endIf
          stagingDir = kwargs.get('stagingDirPath')
          if (not stagingDir):
            raise MissingArgumentException("If the kubectl command includes a -f option, a staging directory path (stagingDirPath) keyword argument must be provided.")
          #endIf
          value = self.processFileOption(stagingDir,value,cmdDocs[1])
        #endIf
        # TBD: special processing for other options goes here
        cmdList.append(value)
        cmdStr = "%s %s" % (cmdStr,value)
      #endFor
    #endIf
    
    return {'cmdList': cmdList, 'cmdString': cmdStr}
  #endDef
    
#endClass