"""
Created on Nov 15, 2018

@author: Peter Van Sickel - pvs@us.ibm.com
"""

import os, fnmatch, yaml
from subprocess import call

from yapl.utilities.Trace import Trace, Level
from yapl.exceptions.Exceptions import InvalidParameterException
from yapl.exceptions.Exceptions import MissingArgumentException
from yapl.exceptions.Exceptions import InvalidConfigurationFile
from yapl.exceptions.ICPExceptions import CommandInterpreterException

# Imports or command helpers
from yapl.k8s.KubectlHelper import KubectlHelper
from yapl.helm.HelmHelper import HelmHelper

TR = Trace(__name__)

"""
  CommandHelpers maps commands to their helper class
"""
CommandHelpers = { 
  "kubectl": KubectlHelper,
  "helm": HelmHelper
}

class CommandHelper(object):
  """
    CommandHelper assists in the execution of commands defined in yaml files in a directory
    referred to as the command directory.
    
    The order of the yaml files in the directory is the order in which the commands are executed.
      
  """

  IntrinsicVariables = {}
  IntrinsicVariableNames = []
  
  def __init__(self, commandPath=None, intrinsicVariables=None, **restArgs):
    """
      Constructor
      
      commandPath - path to directory that holds the command definition yaml files
      instrinsicVariables - dictionary of name-value pairs for variables defined by the framework

      restArgs:
      
        restArgs may have values for custom variables that override the 
        custom variable values in the variables yaml
        
            
    """
    methodName = '__init__'
    
    object.__init__(self)
    
    if (not commandPath):
      raise MissingArgumentException("The command path must be provided.")
    #endIf

    self.commandPath = commandPath
    
    if (intrinsicVariables):
      self.IntrinsicVariables = intrinsicVariables.copy()
      self.IntrinsicVariableNames = self.IntrinsicVariables.keys()
    #endIf
    
    self.home = os.path.expanduser('~')
      
    # command path may have no variables (static command)
    self.variableValues = {}
    self.variableMap = {}
    
    variablesFiles = self.getYaml(self.commandPath, include=['variables'])
    if (not variablesFiles):
      if (TR.isLoggable(Level.FINEST)):
        TR.finest(methodName,"No yaml found for kind variables; static command set use-case.")
      #endIf
    else:
      if (len(variablesFiles) > 1):
        TR.warning(methodName, "Multiple variables files is currently not supported.  Only the first variables file will be used.")
      #endIf
      
      # Only the first file of kind variables is processed      
      variablesPath = variablesFiles[0]
      if (TR.isLoggable(Level.FINEST)):
        TR.finest(methodName,"Using variables defined in: %s" % variablesPath)
      #endIf
         
      with open(variablesPath, 'r') as variablesFile:
        variables = yaml.load(variablesFile)
      #endWith
            
      variableMap = variables.get('VariableKeywordMap')
      if (not variableMap):
        raise InvalidConfigurationFile("The file: %s, is expected to have a VariableKeywordMap attribute." % variablesPath )
      #endIf
      
      if (TR.isLoggable(Level.FINEST)):
        TR.finest(methodName,"Variable Keyword Map: %s" % variableMap)
      #endIf
      
      self.variableMap = variableMap
      self.variableNames = variableMap.keys()
      
      # Custom VariableValues are optional, could be using only IntrinsicVariables.
      variableValues = variables.get('VariableValues')
      
      if (variableValues):
        if (TR.isLoggable(Level.FINEST)):
          TR.finest(methodName,"Custom Variable Values: %s" % variableValues)
        #endIf
      else:
        if (TR.isLoggable(Level.FINEST)):
          TR.finest(methodName,"No custom variable values defined.")
        #endIf
      #endIf
      
      if (restArgs):
        self.variableValues = self.mergeArgValues(self.variableNames, variableValues, **restArgs)
      else:
        self.variableValues = variableValues
      #endIf
      
      if (self.IntrinsicVariables):
        self.variableValues = self.mergeArgValues(self.variableNames,self.variableValues,**self.IntrinsicVariables)
      #endIf
      
      if (TR.isLoggable(Level.FINEST)):
        TR.finest(methodName,"All Variable Values: %s" % self.variableValues)
      #endIf
      
    #endIf      
  #endDef
  
  
  def __getattr__(self,attributeName):
    """
      Support for attributes that are defined in the IntrinsicVariableNames list
      and with values in the IntrinsicVariables dictionary.  
    """
    attributeValue = None
    if (attributeName in self.IntrinsicVariableNames):
      attributeValue = self.IntrinsicVariables.get(attributeName)
    else:
      raise AttributeError("%s is not an IntrinsicVariableName" % attributeName)
    #endIf
  
    return attributeValue
  #endDef


  def __setattr__(self,attributeName,attributeValue):
    """
      Support for attributes that are defined in the IntrinsicVariableNames list
      and with values in the IntrinsicVariables dictionary.
      
      NOTE: The IntrinsicVariables are intended to be read-only.  This method is
      here for completeness.
    """
    if (attributeName in self.IntrinsicVariableNames):
      self.IntrinsicVariables[attributeName] = attributeValue
    else:
      object.__setattr__(self, attributeName, attributeValue)
    #endIf
  #endDef

  
  def mergeArgValues(self, variableNames, variableValues, **restArgs):
    """
      Return a reference to the variableValues dictionary with merged values for 
      the variableNames from restArgs
      
      For each name in the variableNames list, check the restArgs to see if there
      is a value to use to update a name-value pair variableValues dictionary.
      The value of a given variable in restArgs takes precedence over the value
      that is defined in the variables yaml.
      
    """
    methodName = 'mergeArgValues'
    
    for name in variableNames:
      value = restArgs.get(name)
      if (value != None):
        if (variableValues.get(name) != None):
          if (TR.isLoggable(Level.FINEST)):
            TR.finest(methodName,"Replacing value of %s: %s with: %s" % (name,variableValues[name],value))
          #endIf
          variableValues[name] = value
        else:
          # typically this would be adding a value for an intrinsic variable
          if (TR.isLoggable(Level.FINEST)):
            TR.finest(methodName,"Adding variable value: %s: %s" % (name,value))
          #endIf
          variableValues[name] = value
      #endIf
    #endFor
        
    return variableValues
  #endDef


  def checkForMacros(self,line,parameterNames,keywordMap):
    """
      Return a dictionary with one or more key-value pairs from the keywordMap that 
      have a macro substitution present in the given line.
      
      If parameterNames or keywordMap is empty (or None) then nothing to do and an
      empty result is returned.  A static command file would have no parameters.
        
      Otherwise, return an empty dictionary. 
    """
    result = {}
    if (parameterNames and keywordMap):
      for parmName in parameterNames:
        macroName = keywordMap.get(parmName)
        if (not macroName):
          raise InvalidParameterException("The parameter name: %s was not found in the given keyword mappings hash map: %s" % (parmName,keywordMap))
        #endIf
        macro = "${%s}" % macroName
        if (line.find(macro) >= 0):
          result[parmName] = macroName
        #endIf
      #endFor
    #endIf
    return result
  #endDef
  

  def createCommandFile(self, commandFilePath=None, templateFilePath=None, **restArgs):
    """      
      Using the template file, fill in all the variable strings in the template
      using the given parameters.
      
      Optional restArgs:
        parameters: Dictionary with the actual values of the parameters
                    The parameter values will be substituted for the corresponding
                    macro in the template file to create the configuration file.
        
        keywordMap: The mapping of parameter names to macro names (keywords) in the
                    template file.
                    
        specialValues: Dictionary used for macro name that requires a special format  
                       string to be used when doing the macro substitution.
                       Defaults to an empty dictionary.
            
      Comment lines in the template file are written immediately to the command file.
      
      A macro in the template file is delimited by ${} with the macro name in the {}.
      
    """
    methodName = "createCommandFile"
    
    if (not commandFilePath):
      raise MissingArgumentException("The command file path must be provided.")
    #endIf
    
    if (not templateFilePath):
      raise MissingArgumentException("The template file path must be provided.")
    #endIf
  
    parameters = restArgs.get('parameters')
    if (parameters):   
      if (TR.isLoggable(Level.FINEST)):
        TR.finest(methodName,"Parameters: %s" % parameters)
      #endIf
      parameterNames = parameters.keys()
    else:
      parameterNames = []
    #endIf
    
    keywordMap = restArgs.get('keywordMap',{})
    if (keywordMap):
      if (TR.isLoggable(Level.FINEST)):
        TR.finest(methodName,"Keyword Map: %s" % keywordMap)
      #endIf
    #endIf
    
    if (parameterNames and not keywordMap):
      raise InvalidParameterException("A keyword map must be provided if there are substitution parameters")
    #endIf
    
    if (keywordMap and not parameterNames):
      parameterNames = keywordMap.keys()
    #endIf
    
    specialValues = restArgs.get('specialValues',{})
    specialValueNames = specialValues.keys()
        
    try:
      with open(templateFilePath,'r') as templateFile, open(commandFilePath,'w') as commandFile:
        for line in templateFile:
          # Need to strip at least the newline character(s)
          line = line.rstrip()
          if (line.startswith('#')):
            commandFile.write("%s\n" % line)
          else:
            if (TR.isLoggable(Level.FINEST)):
              TR.finest(methodName,"Checking line for macros: %s" % line)
            #endIf
            
            substitutions = self.checkForMacros(line,parameterNames,keywordMap)
            
            if (not substitutions):
              commandFile.write("%s\n" % line)
            else:
              if (TR.isLoggable(Level.FINEST)):
                TR.finest(methodName,"Substitutions: %s" % substitutions)
              #endIf
            
              parmNames = substitutions.keys()
              
              for parmName in parmNames:
                macroName = substitutions[parmName]
                parmValue = parameters[parmName]
                if (specialValueNames and macroName in specialValueNames):
                  specialFormat = specialValues.get(macroName)
                  parmValue = specialFormat.format(parmValue)
                #endIf
                macro = "${%s}" % macroName
                if (TR.isLoggable(Level.FINEST)):
                  TR.finest(methodName,"LINE: %s\n\tReplacing: %s with: %s" % (line,macro,parmValue))
                #endIf
                line = line.replace(macro,"%s" % parmValue)
              #endFor

              if (TR.isLoggable(Level.FINEST)):
                TR.finest(methodName,"NEW LINE: %s" % line)
              #endIf
              
              commandFile.write("%s\n" % line)
            #endIf
          #endIf
        #endFor
      #endWith 
    except IOError as e:
      TR.error(methodName,"IOError creating command file: %s from template file: %s" % (commandFilePath,templateFilePath), e)
      raise
    #endTry
  #endDef

  
  def createCommands(self,commandPath):
    """
      Return list of command dictionaries where each command dictionary has the command
      in the form of a list and a string.  Either the list or the string can be used 
      with subprocess.call().  The command string is useful emitting trace.
      
      Each command dictionary looks like:
      { cmdList: [ ... ], cmdString: "..." }
      
      A list of command dictionaries is returned as there may be more than one command
      defined in the commandPath directory.  The ordering of the commands in the list is
      the order of the template files in the commandPath directory.
      
      Each command is defined by the .yaml command template and the substitution of actual  
      values for the macro expressions in the templates.
      
      The commands are sorted based on a simple string sort of the file names in the commandPath.
    """
    methodName = "createCommands"
    
    commands = []
    
    cmdTemplates = self.getYaml(commandPath,exclude=['variables'])
    if (not cmdTemplates):
      TR.warning(methodName,"No command template files found in: %s" % commandPath)
    else:
      stagingDir = os.path.join(os.getcwd(),'staging')
      # Command files get created in the staging directory.
      if (not os.path.exists(stagingDir)):
        os.mkdir(stagingDir)
      #endIf
      
      if (len(cmdTemplates) > 1): cmdTemplates.sort()
      
      for template in cmdTemplates:
        baseName = os.path.basename(template)
        rootName,ext = os.path.splitext(baseName)
        cmdFilePath = os.path.join(stagingDir,"%s-command%s" % (rootName,ext))
        
        self.createCommandFile(commandFilePath=cmdFilePath,
                              templateFilePath=template,
                              parameters=self.variableValues,
                              keywordMap=self.variableMap)
        
        with open(cmdFilePath, 'r') as cmdFile:
          cmdDocs = list(yaml.load_all(cmdFile))
        #endWith
        
        cmdDoc0  = cmdDocs[0]
        cmdKind = cmdDoc0.get('kind')
        
        helperClass = CommandHelpers.get(cmdKind)
        if (not helperClass):
          raise CommandInterpreterException("CommandHelpers has no helper class for command kind: %s" % cmdKind)
        #endIf
        helper = helperClass()
        cmd = helper.createCommand(cmdDocs,stagingDirPath=stagingDir)
              
        commands.append(cmd)
      #endFor
    #endIf    
    return commands
  #endDef
  
  
  def invokeCommands(self, **restArgs):
    """
      Process the configuration files and invoke the commands.
    """
    methodName = 'invokeCommands'
    
    TR.entering(methodName)
    
    if (restArgs):
      self.variableValues = self.mergeArgValues(self.variableNames, self.variableValues, **restArgs)
      if (TR.isLoggable(Level.FINEST)):
        TR.finest(methodName,"Using variable values: %s" % self.variableValues)
      #endIf
    #endIf
    
    try:
      commands = self.createCommands(self.commandPath)
      if (commands):
        for command in commands:
          if (TR.isLoggable(Level.FINEST)):
            TR.finest(methodName,"Command: %s" % command)
          #endIf
          cmdStr = command.get('cmdString')
          cmdList = command.get('cmdList')
          TR.info(methodName, "Invoking: %s" % cmdStr)
          retcode = call(cmdList)
          if (retcode != 0):
            raise Exception("Invoking: '%s' Return code: %s" % (cmdStr,retcode))
          #endIf
        #endFor
      #endIf
    except Exception as e:
      TR.error(methodName,"ERROR: %s" % e, e)
      raise
    #endTry    
    
    TR.exiting(methodName)
  #endDef
  
  
  def includeYaml(self, kind, include=[], exclude=[]):
    """
      Return True if the given kind is in the include list and not in the exclude list.
      
      If both include and exclude are empty then True is returned.
      
      If include has members and exclude is empty then True is returned only if kind is in the include list.
      If include is empty and exclude has members, then True is returned as long as kind is not a member of exclude.
      
      If both include and exclude have members, then True is returned only if kind is in the include list and 
      not in the exclude list.
    """
    
    if (not include and not exclude): return True
    if (include and not exclude): return kind in include
    if (not include and exclude): return kind not in exclude
    if (include and exclude): return kind in include and kind not in exclude
  #endIf
  
  
  def getYaml(self, dirPath, include=[], exclude=[]):
    """
      Return a list of full paths to all the .yaml files in the given dirPath directory. 
      
      dirPath - Path to the directory of yaml files to be considered.  (only .yaml files are considered)
      
      include - a list of names of the kind of yaml file to be included in the result set.
      exclude - a list of names of the kind of yaml file to be excluded from the result set.
      
      If include and exclude are both empty, then the result set includes all .yaml files in 
      the given dirPath directory.
      
      If either include or exclude have members, then if a yaml file does not have a kind 
      attribute, it is not included in the result set.
      
      See includeYaml() for a description of the include and exclude lists to be used as filters for
      the kind of yaml files to include in the returned list.
      
      For different approaches to listing files in a directory see:
      See https://stackabuse.com/python-list-files-in-a-directory/
      
      NOTE: The yaml.load_all() method returns a generator.  In the code below that
      gets converted to a list for convenience.
    """
    methodName="getYaml"
    
    files = os.listdir(dirPath)
    
    pattern = "*.yaml"
    yamlFiles = [os.path.join(dirPath,f) for f in files if fnmatch.fnmatch(f,pattern)]

    if (include or exclude):
            
      if (include and TR.isLoggable(Level.FINEST)):
        TR.finest(methodName,"Yaml files to be included: %s" % include)
      #endIf
    
      if (exclude and TR.isLoggable(Level.FINEST)):
        TR.finest(methodName,"Yaml files to be excluded: %s" % exclude)
      #endIf
    
      if (TR.isLoggable(Level.FINEST)):
        TR.finest(methodName,"Yaml files to consider: %s" % yamlFiles)
      #endIf
      
      includedFiles = []
      for f in yamlFiles:
        with open(f, 'r') as yamlFile:
          docs = list(yaml.load_all(yamlFile))
        #endWith
        
        # we only care about the first doc in the file
        doc = docs[0]
        
        kind = doc.get('kind')
        if (kind and self.includeYaml(kind,include,exclude)):
          includedFiles.append(f)
        #endIf
      #endFor
            
      yamlFiles = includedFiles
    #endIf
    
    if (TR.isLoggable(Level.FINEST)):
      TR.finest(methodName,"Included yaml files: %s" % yamlFiles)
    #endIf
    
    return yamlFiles
  #endDef
  
#endClass
        