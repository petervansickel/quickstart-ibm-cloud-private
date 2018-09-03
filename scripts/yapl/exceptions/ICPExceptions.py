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
Created on Aug 10, 2018

@author: Peter Van Sickel - pvs@us.ibm.com
'''

class ICPInstallationException(Exception):
  """
    ICPInstallationException is raised when something unexpected occurs at some 
    point in the installation scripting, after the CloudFormation stack deployment.
  """
#endClass
