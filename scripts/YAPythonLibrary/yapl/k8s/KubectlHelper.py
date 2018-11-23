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
import os, fnmatch
from subprocess import call
import yaml
from yapl.utilities.Trace import Trace, Level
from yapl.exceptions.Exceptions import InvalidArgumentException
from yapl.exceptions.Exceptions import MissingArgumentException
from yapl.exceptions.Exceptions import InvalidParameterException
from yapl.exceptions.Exceptions import InvalidConfigurationException
from yapl.exceptions.Exceptions import InvalidConfigurationFile

TR = Trace(__name__)


class KubectlHelper(object):
  """
    Helper class to support the execution of kubectl commands targeted at an ICP cluster.
    
    The primary role of the class is to support the createCommand() method given a 
    list of yaml documents.
    
    This class supports the CommandHelper class.
    
  """

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
  
  
  def createCommands(self,configPath):
    """
      Return list of command dictionaries where each command dictionary has the command
      in the form of a list and a string.  Either the list or the string can be used 
      with subprocess.call().  The command string is useful emitting trace.
      
      Each command dictionary looks like:
      { cmdList: [ ... ], cmdString: "..." }
      
      A list of command dictionaries is returned as there may be more than one helm command
      defined in the configPath directory.  The ordering of the commands in the list is
      the order of the helm template files in the configPath directory.
      
      Each command is defined by the .yaml command template and the substitution of actual  
      values for the macro expressions in the templates.
    """
    
    commands = []
    
    stagingDir = os.path.join(os.getcwd(),'staging')
    if (not os.path.exists(stagingDir)):
      os.makedirs(stagingDir)
    #endIf
    
    cmdTemplates = self.getYaml(configPath,'kubectl')
    for template in cmdTemplates:
      baseName = os.path.basename(template)
      rootName,ext = os.path.splitext(baseName)
      cmdFilePath = os.path.join(stagingDir,"%s-command%s" % (rootName,ext))
      
      self.createCommandFile(commandFilePath=cmdFilePath,
                            templateFilePath=template,
                            parameters=self.variableValues,
                            keywordMap=self.variableMap)
      
      cmdStr = "kubectl"
      cmdList = [ 'kubectl' ]
      
      with open(cmdFilePath, 'r') as cmdFile:
        docs = list(yaml.load_all(cmdFile))
      #endWith
      
      cmdDoc  = docs[0]
      
      command = cmdDoc.get('command')
      if (not command):
        raise InvalidConfigurationFile("The first yaml document in %s, must have a command attribute." % cmdFilePath)
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
            if (len(docs) < 2):
              raise InvalidConfigurationFile("Expecting a second document to be used with the -f option in command file: %s ." % cmdFilePath)
            #endIf
            value = self.processFileOption(stagingDir,value,docs[1])
          #endIf
          # TBD: special processing for other options goes here
          cmdList.append(value)
          cmdStr = "%s %s" % (cmdStr,value)
        #endFor
      #endIf
      
      commands.append({'cmdList': cmdList, 'cmdString': cmdStr})
    #endFor
    return commands
  #endDef
    
#endClass