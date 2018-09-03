"""
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

Created on Aug 6, 2018

@author: Peter Van Sickel - pvs@us.ibm.com
"""

import boto3
from yapl.utilities.Trace import Trace, Level
from yapl.exceptions.Exceptions import MissingArgumentException
from yapl.exceptions.Exceptions import InvalidParameterException
from yapl.exceptions.AWSExceptions import AWSStackResourceException
from yapl.exceptions.ICPExceptions import ICPInstallationException

TR = Trace(__name__)

# NOTE: The key names for TemplateKeywordMapping must be alpha-numeric characters only.
#       The key names are the parameter names used in the CloudFormation template that 
#       deploys the ICP cluster resources.
TemplateKeywordMappings = {
                           'CalicoTunnelMTU':      'CALICO_TUNNEL_MTU',
                           'CloudProvider':        'CLOUD_PROVIDER',
                           'ClusterCADomain':      'CLUSTER_CA_DOMAIN',
                           'ClusterCIDR':          'CLUSTER_CIDR',
                           'ClusterDomain':        'CLUSTER_DOMAIN',
                           'ClusterLBAddress':     'CLUSTER_LB_ADDRESS',
                           'ClusterName':          'CLUSTER_NAME',
                           'ExcludedMgmtServices': 'EXCLUDED_MGMT_SERVICES',
                           'KubletNodeName':       'KUBLET_NODENAME',
                           'ProxyLBAddress':       'PROXY_LB_ADDRESS',
                           'ServiceCIDR':          'SERVICE_CIDR'
                          }

ConfigurationParameterNames = TemplateKeywordMappings.keys()

AWSDefaultParameterValues = {
                              'CalicoTunnelMTU': 8981,
                              'CloudProvider': 'aws',
                              'ExcludedMgmtServices': ["istio", "vulnerability-advisor", "custom-metrics-adapter"],
                              'KubletNodeName': 'fqdn'
                            }

# ELB names in the AWS stack
MasterNodeLoadBalancer = 'MasterNodeLoadBalancer'
ProxyNodeLoadBalancer = 'ProxyNodeLoadBalancer'

OptionalManagementServices = ["service-catalog", "metering", "monitoring", "istio", "vulnerability-advisor", "custom-metrics-adapter" ]


class ConfigureICP:
  """
    Class that supports the manipulation of a config.yaml template file that
    gets used to drive the installation of IBM Cloud Private (ICP).
  """

  def __init__(self, stackIds=None, templatePath=None, **restArgs):
    """
      Constructor
      
      The stackIds input parameter is expected to be a list of AWS stack resource IDs.
      The first stack ID in the list is assumed to be the root stack.
    """
    methodName = "__init__"
    
    self.cfnResource = boto3.resource('cloudformation')
    self.cfnClient = boto3.client('cloudformation')
    self.elbv2Client = boto3.client('elbv2')
    
    self.parameters = {}
    
    if (not stackIds):
      raise MissingArgumentException("The CloudFormation stack resource IDs must be provided.")
    #endIf
    
    self.rootStackId = stackIds[0]
    
    if (not templatePath):
      raise MissingArgumentException("The path to the config.yaml template file must be provided.")
    #endIf
    
    self.templatePath = templatePath
    
    stackParms = self.getStackParameters(self.rootStackId)
    if (TR.isLoggable(Level.FINEST)):
      TR.finest(methodName,"Parameters defined in the stack:\n\t%s" % stackParms)
    #endIf
    
    self.parameters = self.fillInDefaultValues(**stackParms)
    if (TR.isLoggable(Level.FINEST)):
      TR.finest(methodName,"All parameters, including defaults:\n\t%s" % self.parameters)
    #endIf

    masterELB = self.getLoadBalancerDNSName(stackIds,elbName="MasterNodeLoadBalancer")
    if (not masterELB):
      raise ICPInstallationException("An ELB with a Name tag of MasterNodeLoadBalancer was not found.")
    #endIf
    self.parameters['ClusterLBAddress'] = masterELB
    
    proxyELB = self.getLoadBalancerDNSName(stackIds,elbName="ProxyNodeLoadBalancer")
    if (not proxyELB):
      raise ICPInstallationException("An ELB with a Name tag of ProxyNodeLoadBalancer was not found.")
    #endIf
    self.parameters['ProxyLBAddress'] = proxyELB
    
    self.parameters['ClusterCADomain'] = self.getCommonName()
    
    self.parameterNames = self.parameters.keys()    
  #endDef
  
  
  def getStackParameters(self, stackId):
    """
      Return a dictionary with stack parameter name-value pairs for
      stack parameters relevant to the ICP Configuration from the  
      CloudFormation stack with the given stackId.
      
      Only stack parameters with names in the ConfigurationParameterNames list
      are included in the result set.
    """
    result = {}
    
    stack = self.cfnResource.Stack(stackId)
    stackParameters = stack.parameters
    for parm in stackParameters:
      parmName = parm['ParameterKey']
      if (parmName in ConfigurationParameterNames):
        result[parmName] = parm['ParameterValue']
      #endIf
    #endFor
    
    return result
  #endDef
  
  
  def fillInDefaultValues(self, **restArgs):
    """
      Return a dictionary that is a combination of values in restArgs and 
      default parameter values in AWSDefaultParameterValues.
    """
    
    result = {}
    defaultValues = AWSDefaultParameterValues
    
    for parmName in ConfigurationParameterNames:
      parmValue = restArgs.get(parmName,defaultValues.get(parmName))
      if (parmValue):
        result[parmName] = parmValue
      #endIf
    #endFor

    return result
  #endDef
  
  
  def getCommonName(self):
    """
      Get the CommonName from the ClusterCADomain stack parameter or 
      a combination of the ClusterName and ClusterDomain stack parameters.
    """
    CN = self.parameters['ClusterCADomain']
    if (not CN):
      CN = "%s.%s" % (self.parameters['ClusterName'],self.parameters['ClusterDomain'])
    #endIf
    return CN
  #endDef
  
  
  def listELBResoures(self,stackId):
    """
      Return a list of ELB resource instance IDs from the given stack.
      
      An empty list is returned if there are no ELB instances in the given stack.
    """
    
    if (not stackId):
      raise MissingArgumentException("A stack ID (stackId) is required.")
    #endIf

    response = self.cfnClient.list_stack_resources(StackName=stackId)
    if (not response):
      raise AWSStackResourceException("Empty result for CloudFormation list_stack_resources for stack: %s" % stackId)
    #endIf
    
    stackResources = response.get('StackResourceSummaries')
    if (not stackResources):
      raise AWSStackResourceException("Empty StackResourceSummaries in response from CloudFormation list_stack_resources for stack: %s." % stackId)
    #endIf

    elbIIDs = []
    for resource in stackResources:
      resourceType = resource.get('ResourceType')
      if (resourceType == 'AWS::ElasticLoadBalancingV2::LoadBalancer'):
        elbInstanceId = resource.get('PhysicalResourceId')
        elbIIDs.append(elbInstanceId)        
      #endIf
    #endFor

    return elbIIDs
  #endDef
    
  
  def getELBResourceIdForName(self,stackId,elbName=None):
    """
      Return the Elastic Load Balancer ARN with the given name as the value of its Name tag.
      
      If no ELB is found with the given name in its Name tag then the empty string is returned.
    """
    if (not stackId):
      raise MissingArgumentException("A stack ID (stackId) is required.")
    #endIf

    if (not elbName):
      raise MissingArgumentException("An Elastic Load Balancer Name (elbName) must be provided.")
    #endIf
    
    elbResourceId = ""
    
    elbIIds = self.listELBResoures(stackId)
    
    if (elbIIds):
      for elbIId in elbIIds:
        response = self.elbv2Client.describe_tags(ResourceArns=[elbIId])
        if (not response):
          raise AWSStackResourceException("Empty response for ELBv2 Client describe_tags() for Elastic Load Balancer with ARN: %s" % elbIId)
        #endIf
      
        tagDescriptions = response.get('TagDescriptions')
        if (len(tagDescriptions) != 1):
          raise AWSStackResourceException("Unexpected number of TagDescriptions in describe_tags() response from ELB with ARN: %s" % elbIId)
        #endIf
        
        tagDescription = tagDescriptions[0]
        tags = tagDescription.get('Tags')
        if (not tags):
          raise AWSStackResourceException("All Elastic Load Balancers must have at least a Name tag.  No tags found for ELB with ARN: %s" % elbIId)
        #endIf
        
        for tag in tags:
          if (tag.get('Key') == 'Name'):
            if (tag.get('Value') == elbName):
              elbResourceId = tagDescription.get('ResourceArn')
              break
            #endIf
          #endIf
        #endFor
        
        if (elbResourceId): break
      #endFor
    #endIf
    
    return elbResourceId
  #endDef
  
  
  def getLoadBalancerDNSName(self,stackIds,elbName=None):
    """
      Return the DNSName for the Elastic Load Balancer V2 with the given name as the value
      of its Name tag.
      
      The stackIds parameter holds the list of all the stacks in the CFN deployment.  
      It is assumed there is only 1 ELB in all of those stacks with the given name.
      (The DNSName of the first one found with the given name gets returned.)
      
      The boto3 API for ELBs is rather baroque.
      
      The tags are gotten using the describe_tags() method.  We need to look at the tags
      in order to find the ELB with Name tag value for the given name (elbName).  The 
      response from the describe_tags() call also includes the ARN (reource Id) for 
      the ELB with the set of tags.
      
      Once we have the ELB ARN, we can get its DNSName with a call to describe_load_balancers().
    """
    
    if (not stackIds):
      raise MissingArgumentException("A list of stack IDs (stackIds) is required.")
    #endIf
    
    if (not elbName):
      raise MissingArgumentException("The ELB name must be provided.")
    #endIf

    dnsName = ""
    
    for stackId in stackIds:
      elbIId = self.getELBResourceIdForName(stackId, elbName=elbName)
      
      if (elbIId):
        response = self.elbv2Client.describe_load_balancers(LoadBalancerArns=[elbIId])
        if (not response):
          raise AWSStackResourceException("Empty response for ELBv2 Client describe_load_balancers() call for ELB with ARN: %s" % elbIId)
        #endIf
    
        loadBalancers = response.get('LoadBalancers')
        if (not loadBalancers):
          raise AWSStackResourceException("No LoadBalancers in response for ELBv2 Client describe_load_balancers() call for ELB with ARN: %s" % elbIId)
        #endIf
    
        if (len(loadBalancers) != 1):
          raise AWSStackResourceException("Unexpected number of LoadBalancers from ELBv2 Client describe_load_balancers() call for ELB with ARN: %s" % elbIId)
        #endIf
    
        loadBalancer = loadBalancers[0]
    
        dnsName = loadBalancer.get('DNSName')
        if (not dnsName):
          raise AWSStackResourceException("Empty DNSName attribute for ELB with ARN: %s" % elbIId)
        #endIf
        break
      #endIf
    #endFor
    
    return dnsName
  #endDef
  
  
  def _checkForParm(self,line,parameterNames):
    """
      Return a tuple (parmName,maccroName) if the given line has a substitution macro using 
      a keywords (macroName) for one the parameter names given in parameterNames  Otherwise return None.  
      
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
  
  
  def _transformExcludedMgmtServices(self,excludedServices):
    """
      Return a list of strings that are the names of the services to be excluded.
      
      The incoming excludedServices parameter may be a list of strings or the string
      representation of a list using commas to delimit the items in the list.
      (The value of ExcludedMgmtServices in the AWS CF template is a CommaDelimitedList 
      which is just such a string.)
      
      The items in the incoming list are converted to all lowercase characters and trimmed.
      
      If the incoming value in excludedServices is the empty string, then an empty list
      is returned.
    """
    
    result = []
    if (excludedServices):
      if (type(excludedServices) != type([])):
        # assume excludedServices is a string
        excludedServices = [x.strip() for x in excludedServices.split(',')]
      #endIf
      
      excludedServices = [x.lower() for x in excludedServices]
      
      for x in excludedServices:
        if (x not in OptionalManagementServices):
          raise ICPInstallationException("Service: %s is not an optional management service.  It must be one of: %s" % (x,OptionalManagementServices))
        #endIf
      #endFor
      
      result = excludedServices
    #endIf
    return result
  #endDef
  
  
  def createConfigFile(self, configFilePath):
    """
      Using the configuration file template, fill in all the variable strings in the template
      using the parameters provided to the instance.
      
      Comment lines in the template file are written immediately to the configuration file.
      
      NOTE: It is assumed that a line in the configuration template file has at most
      one parameter defined in it.  A parameter is delimited by ${} with the parameter
      name in the {}.
      
      NOTE: It is assumed a given parameter only appears once in the configuration file
      template. Once a parameter has been found and replaced in a given line in the template
      file, there is no need to check other lines for that same parameter.
    """
    methodName = "createConfigFile"
    
    parameterNames = self.parameterNames
    
    try:
      with open(self.templatePath,'r') as templateFile, open(configFilePath,'w') as configFile:
        for line in templateFile:
          line = line.strip()
          if (line.startswith('#')):
            configFile.write("%s\n" % line)
          else:
            parmName,macroName = self._checkForParm(line,parameterNames)
            if (not parmName):
              configFile.write("%s\n" % line)
            else:
              parmValue = self.parameters[parmName]
              # special processing for excluded mgmt services value
              if (parmName == 'ExcludedMgmtServices'):
                parmValue = self._transformExcludedMgmtServices(parmValue)
              #endIf
              macro = "${%s}" % macroName
              if (TR.isLoggable(Level.FINEST)):
                TR.finest(methodName,"LINE: %s\n\tReplacing: %s with: %s" % (line,macro,parmValue))
              #endIf
              newline = line.replace(macro,"%s" % parmValue)
              if (TR.isLoggable(Level.FINEST)):
                TR.finest(methodName,"NEW LINE: %s" % newline)
              #endIf
              configFile.write("%s\n" % newline)
              # No need to keep checking for parmName, once it has been found in a line in the template.
              parameterNames.remove(parmName)
            #endIf
          #endIf
        #endFor
      #endWith 
    except IOError as e:
      TR.error(methodName,"IOError creating configuration file: %s from template file: %s" % (configFilePath,self.tempatePath), e)
      raise
    #endTry
    
  #endDef
  
#endClass