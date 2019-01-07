"""
Created on Nov 2, 2018

@author: Peter Van Sickel - pvs@us.ibm.com

DESCRIPTION:
  Module to assist with programmatically executing helm commands in Python.
  
NOTES:
  The implementation originated as a generalized way to run helm installations.
  The implementation has only been tested in a very limited scope in the context
  of installing certain applications on ICP.
  
  It is assumed Helm has been installed and configured.
"""


from yapl.utilities.Trace import Trace
from yapl.exceptions.Exceptions import MissingArgumentException


TR = Trace(__name__)


class HelmHelper(object):
  """
    Class to support the installation of applications on an ICP cluster using
    Helm and helm charts.
    
    It is assumed Helm has been installed and is available at the command line.    
  """


  def __init__(self):
    """
      Constructor
    """
    object.__init__(self)
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
      
      Implicit in each command are the following arguments:
        --ca-file
        --cert-file
        --key-file
    """
    if (not cmdDocs):
      raise MissingArgumentException("A non-empty list of command documents (cmdDocs) must be provided.")
    #endIf

    helmCmd = cmdDocs[0]
        
    cmdStr = "helm"
    cmdList = [ 'helm' ]
    
    command = helmCmd.get('command','install')
    
    cmdList.append(command)
    cmdStr = "%s %s" % (cmdStr,command)
    
    #cmdList.extend(["--ca-file", self.ClusterCertPath, "--cert-file", self.HelmCertPath, "--key-file", self.HelmKeyPath])
    #cmdStr = "%s --ca-file %s --cert-file %s --key-file %s" % (cmdStr,self.ClusterCertPath,self.HelmCertPath,self.HelmKeyPath)
    
    flags = helmCmd.get('flags')
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
    
    chart = helmCmd.get('chart')
    if (chart):
      cmdList.append(chart)
      cmdStr = "%s %s" % (cmdStr, chart)
    #endIf

    options = helmCmd.get('options')
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
        cmdList.append(value)
        cmdStr = "%s %s" % (cmdStr,value)
      #endFor
    #endIf
    
    setValues = helmCmd.get('set-values')
    if (setValues):
      setNames = setValues.keys()
      for name in setNames:
        cmdList.append('--set')
        valueStr = "{name}={value}".format(name=name,value=setValues[name])
        cmdList.append(valueStr)
        cmdStr = "%s --set %s" % (cmdStr, valueStr)
      #endFor
    #endIf
      
    return {'cmdList': cmdList, 'cmdString': cmdStr}
  #endDef
    
#endClass
