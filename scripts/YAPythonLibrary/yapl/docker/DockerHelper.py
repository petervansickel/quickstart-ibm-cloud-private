"""
Created on Feb 2, 2019

@author: Peter Van Sickel

Module to support executing Docker commands as defined by yaml.

WARNING: Only a very limited capability is supported.  The bare minimum needed to do ICP installations.

"""

from subprocess import call

from yapl.utilities.Trace import Trace
from yapl.exceptions.Exceptions import MissingArgumentException
from yapl.exceptions.Exceptions import InvalidArgumentException
from yapl.utilities.cd import cd


TR = Trace(__name__)


"""
  DockerCommandArgs holds a list of recognized commands and the names of the 
  attributes in the yaml file that define the command arguments.
  These arguments are "nameless" in the command line. In the yaml, the arguments
  get a name as noted in DockerCommandArgs table.  The arguments are then added
  to the command line in the createCommands() or invokeCommands() methods.
  
  The nameless command arguments are added to the command line in the order
  they are defined in the DockerCommandArgs table.  For example, for the 
  docker run command the image and then the image-command string is added
  to the command in that order. 
  
  The nameless command arguments are added to the command last, i.e., after 
  all other flags, options, env vars, volume bindings, etc.
"""
DockerCommandArgs = {
    'run': ['image', 'image-command']
  }


class DockerHelper(object):
  """
    Class to support running Docker commands based on yaml document 
    command definitions.
  """

  def __init__(self):
    """
      Constructor
    """
    object.__init__(self)
  #endDef
  

  def _invokeCommand(self,cmdList=[],cmdString=""):
    """
      Invoke a single command as specified by cmdList and cmdString
      
      Helper for invokeCommands()
      
      NOTE: From experiments, it was determined that the call() method
      needs to be invoked with shell=True.
    """
    methodName = "_invokeCommand"
    
    if (not cmdList):
      raise MissingArgumentException("A non-empty command list must be provided.")
    #endIf
    
    if (not cmdString):
      raise MissingArgumentException("A non-empty command string must be provided.")
    #endIf
    
    TR.info(methodName, "Invoking: %s" % cmdString)
    #retcode = call(cmdList)
    retcode = call(cmdString,shell=True)
    if (retcode != 0):
      raise Exception("Invoking: '%s' Return code: %s" % (cmdString,retcode))
    #endIf

  #endDef
  
  
  def _flags(self, **kwargs):
    """
      Return a tuple flagList, flagStr to be included in the docker command
      
      The flags to be processed are defined in the kwargs by the flags keyword.
      
      If there are no command flags then ([],"") is returned.
      
      The value of the keyword argument flags is a list of docker command flags.
      A "flag" is an option to a command that has no argument.  A flag argument
      may also be referred to as a "switch".
    """
    
    flagList = []
    flagStr = ""
    
    flags = kwargs.get('flags')
    if (flags):
      for flag in flags:
        if (len(flag) > 1):
          # multi-character flags get a double dash
          flagList.append('--%s' % flag)
          flagStr = "%s --%s" % (flagStr,flag)
        else:
          # single character flags get a single dash
          flagList.append('-%s' % flag)
          flagStr = "%s -%s" % (flagStr,flag)
        #endIf          
      #endFor
    #endIf
    return (flagList,flagStr)
  #endDef
  

  def _options(self, **kwargs):
    """
      Return a tuple optionList, optionStr to be included in the docker command
      
      The options to be processed are defined in the kwargs by the options keyword.
      
      If there are no options then ([],"") is returned.
      
      The value of the options keyword argument is a dictionary of docker command 
      options.  Each key in the dictionary is the option name and the value for 
      the key is the option value.  Command options that may be repeated get 
      special treatment in the command definition yaml file.
      
    """
    optionList = []
    optionStr = ""
    
    options = kwargs.get('options')
    if (options):
      optionNames = options.keys()
      for optionName in optionNames:
        value = options.get(optionName)
        if (len(optionName) > 1):
          optionList.extend(["--%s" % optionName, value])
          if (not optionStr):
            optionStr = "--%s %s" % (optionName,value)
          else:
            optionStr = "%s --%s %s" % (optionStr,optionName,value)
        else:
          optionList.extend(["-%s" % optionName, value])
          optionStr = "%s -%s %s" % (optionStr,optionName,value)
        #endIf
      #endFor
    #endIf
    
    return (optionList,optionStr)
  #endDef


  def load(self, **kwargs):
    """
      Support for the docker load command
      
      Helper for invokeCommands()
    """
    cmdStr = "docker load"
    cmdList = [ 'docker', 'load' ]
    
    optionList,optionStr = self._options(**kwargs)
    
    if (optionList): cmdList.extend(optionList)
    if (optionStr): cmdStr = "%s %s" % (cmdStr,optionStr)  

    chdir = kwargs.get('chdir')
    if (chdir):
      with cd(chdir):
        self._invokeCommand(cmdList=cmdList,cmdString=cmdStr)
      #endWith
    else:    
      self._invokeCommand(cmdList=cmdList,cmdString=cmdStr)
    #endIf
    
  #endDef
   
    
  def run(self,**kwargs):
    """
      Support for the docker run command
      
      Helper for invokeCommands()
    """
    cmdStr = "docker run"
    cmdList = [ 'docker', 'run' ]
    
    flagList,flagStr = self._flags(**kwargs)
    
    if (flagList): cmdList.extend(flagList)
    if (flagStr): cmdStr = "%s %s" % (cmdStr,flagStr)
              

    optionList,optionStr = self._options(**kwargs)
    
    if (optionList): cmdList.extend(optionList)
    if (optionStr): cmdStr = "%s %s" % (cmdStr,optionStr)  
    
    # process environment variables
    env = kwargs.get('env')
    if (env):
      envNames = env.keys()
      for name in envNames:
        valueStr = "{name}={value}".format(name=name,value=env[name])
        cmdList.extend(['-e',valueStr])
        cmdStr = "%s -e %s" % (cmdStr, valueStr)
      #endFor
    #endIf
    
    # process network options
    # WARNING - This only handles simple use-cases, e.g., --net=host
    # Need to fork this into a helper method to handle more complicated cases
    network = kwargs.get('network')
    if (network):
      optionNames = network.keys()
      for optionName in optionNames:
        optionValue = network.get(optionName)
        optionStr = "--%s=%s" % (optionName,optionValue)
        cmdList.append(optionStr)
        cmdStr = "%s %s" % (cmdStr,optionStr)
      #endFor
    #endIf
    
    
    # process volume bind mount options
    volumes = kwargs.get('volumes')
    if (volumes):
      for volume in volumes:
        cmdList.extend(['-v', volume])
        cmdStr = "%s -v %s" % (cmdStr,volume)
      #endFor
    #endIf
    
    # Add the unnamed arguments, if any
    commandArgs = DockerCommandArgs.get('run')
    for argName in commandArgs:
      argValue = kwargs.get(argName)
      if (not argValue):
        raise InvalidArgumentException("The docker run command requires a %s argument." % argName)
      #endIf
      cmdList.append(argValue)
      cmdStr = "%s %s" % (cmdStr, argValue)
    #endFor
  
    chdir = kwargs.get('chdir')
    if (chdir):
      with cd(chdir):
        self._invokeCommand(cmdList=cmdList,cmdString=cmdStr)
      #endWith
    else:    
      self._invokeCommand(cmdList=cmdList,cmdString=cmdStr)
    #endIf
  #endDef
  
  
  def invokeCommands(self,cmdDocs,start,**kwargs):
    """
      Process command docs to invoke each command in sequence that is of kind docker.  

      Processing of cmdDocs stops as soon as a doc kind that is not docker is encountered.

      All cmdDocs that are processed are marked with a status attribute with the value PROCESSED.
             
      cmdDocs - a list of 1 or more YAML documents loaded from yaml.load_all()
      by the caller.
      
      start - index where to start processing in the cmdDocs list.
      
    """
    if (not cmdDocs):
      raise MissingArgumentException("A non-empty list of command documents (cmdDocs) must be provided.")
    #endIf

    for i in range(start,len(cmdDocs)):      
      doc = cmdDocs[i]
      
      kind = doc.get('kind')
      if (not kind or kind != 'docker'): break; # done
      
      command = doc.get('command')
      if (not command):
        raise InvalidArgumentException("A docker command document: %s, must have a command attribute." % doc)
      #endIf

      getattr(self,command)(**doc)
      
      doc['status'] = 'PROCESSED'
      
    #endFor
    
  #endDef
  
  

#endClass