# IBM Cloud Private Deployment Automation Implementation Details

Each ICP node has an ICPRole tag that is used by the bootstrapping
scripts to determine the role of the node.  The following values
for the ICPRole tag and accepted (case insensitive):
  Master, Worker, Proxy, Management, VA, etcd

CloudFormation has a limit on the number of characters in a template of 51200.  Early in the development of the template, that limit was exceeded.  Nested stacks are used to make the template modular and to avoid issues with the character limit.  Nested stacks are more manageable and allow partitioning of development work.

Templates are organized into directories where the directory name represents the version number of the template collection.  The template file name does not include a version number.  One of the input parameters to the deployment is the CloudFormation template version (CFNTemplateVersion).  The value of this parameter must be provided by the deployer. There must be a folder, `templates/_version_`, in the ICPScriptBucketName S3 bucket with all the templates in it, where `_version_` is a placeholder for the actual version.

NIY - The boot node template deploys a bastion host and is a single EC2 instance on the public subnet.

All other templates define a LaunchConfiguration and an AutoScalingGroup for there respective node type.

The templates are organized as follows:

- 00-ibm-cloud-private-root.yaml  
  - the root template, VPC, public subnet, private subnet, gateways and other basic network resources. This template launches all other templates.

- 01-ibm-cloud-private-boot.yaml  
  - the boot node template

- 02-ibm-cloud-private-master.yaml
  - the master node template, master node ELB and other resources associated with the master node.

- 03-ibm-cloud-private-mgmt.yaml
  - the management node template

- 04-ibm-cloud-private-va.yaml
  - the vulnerability advisor template - Not Implemented Yet

- 05-ibm-cloud-private-proxy.yaml
  - the proxy node template

- 06-ibm-cloud-private-worker.yaml
  - the worker node template

- 50-icp-public-subnets.yaml
  - public subnet resource template

- 51-icp-private-subnets.yaml
  - private subnet resource template

- 98-ibm-cloud-private-shared-storage.yaml
  - cluster shared storage

- 99-ibm-cloud-private-iam-security.yaml
  - IAM, host profile, security group resources.  The resources in this template are used by all other nodes.

# Virtual Private Cloud and ICP networks

The CIDR block to use for the VPC must encompass enough usable addresses to include the public and private subnets that will be allocated during the deployment.

The VPCCIDR input parameter encompasses all the subnets.  The default for the VPCCIDR is 10.0.0.0/16.

TBD: The PrivateSubnetCIDR input parameter encompasses all of the private subnets. It is used in the various security group definitions for the private subnets.  

TBD: The PrivateSubnetCIDR may be divided up into 3 or 4 subnets for use in each Availability Zone.

# Using EFS Storage

The cluster has EFS storage configured for shared storage use.

One EFS mount target is deployed in each Availability Zone.

One security group to allow NFS traffic (port 2049) is defined to support EFS as documented here:
https://docs.aws.amazon.com/efs/latest/ug/security-considerations.html#network-access
- SharedStorageSecurityGroup in the shared storage template, `98-ibm-cloud-private-shared-storage.yaml` to allow NFS traffic from the ICP cluster nodes to the mount targets.

*NOTE:* The above documentation is somewhat confusing in that the example shows creating a security group associated with the EC2 instances that allows SSH (port 22) ingress.  In the example, that is merely an expedient to allow the security group ID to be used to specify the `Source` attribute of the NFS ingress rule for the security group associated with the EFS mount targets.  If the CIDR of the EC2 instances is known (which in the case of the ICP cluster it is), then the CIDR should be used for the `Source` attribute of the NFS ingress rule.

*NOTE:* We **do not** use the touted *EFS Mount Helper* as it is only compatible with Amazon Linux AMIs.  Where the documentation describes using the `efs` file system type, it is presuming that the *EFS Mount Helper* is in use.

- An explanation of the mount command to be used for dynamically mounting an EFS volume can be found here: [Mount File System on Your EC2 Instance and Test](https://docs.aws.amazon.com/efs/latest/ug/wt1-test.html#wt1-mount-fs-and-test)

- More information is available here: [Additional Mounting Considerations](https://docs.aws.amazon.com/efs/latest/ug/mounting-fs-mount-cmd-general.html)

- This section describes the use of a standard file system (e.g., nfs4): [Mounting File Systems Without the EFS Mount Helper](https://docs.aws.amazon.com/efs/latest/ug/mounting-fs-old.html)

# CloudFormation details

## YAML vs JSON

It is strongly recommended that YAML be used for CloudFormation templates rather than JSON.  

Advantages of YAML:
- Less verbose syntax (quotes and braces go away)
- Comments are permitted
- More concise expression of constructs
- More syntax options for the expression of constructs
- Easier to spot syntax problems
- Easier to read
- Easier to edit

We started out using JSON.  At some point the template files were getting to be difficult to read and edit due to the complexity of content.  A switch was made to YAML to greatly simplify the syntax and to allow for comments.

## Parameter typing

CloudFormation defines "complex" types such as `CommaDelimitedList` and list types for things like Availability Zone names.  Do not use these complex types in parameter definitions.  The intrinsic functions are not prepared to handle the complex types. A significant example is the `Fn::Split` function can only handle a `String` type in the second argument position.  The `Fn::Split` function is frequently used to form a list from a comma delimited string.  Oddly, `Fn::Split` causes a cryptic "template error" when its second argument is of type `CommaDelimitedList`.

Be very careful about using the various parameter types other than the simple types, i.e., String, Number.

## Parameter passing to child templates

It is best to pass in all parameters used by the child templates.  Unexpected behavior may occur if some parameters in a child template have a default value.

## Default values

It is best to only define default values for parameters in the root stack.

Do not define default values for parameters in child templates.  This will ensure that all parameter values are defined when the child template is invoked by its invoking template.  

If default values are defined in the child templates you may end up with parameters that have a value that was not passed in from the root stack.  The parent stack is incorrectly not passing in a given parameter that has a default value in the child template. Since the parameter has a default value in the child template a problem does not show up immediately in testing.  The missing parameter may not be discovered until possibly very late in testing.

## S3 URLs

Pay no attention to the documentation regarding the structure of S3 URLs.  The primary rule to stick to with S3 URLs:
- *Do not include a reference to an AWS region in the host name part of the URL.*  

There are two styles of S3 URL:
- path-style: `https://s3.amazonaws.com/${BucketName}/${Key}`
or:
- host-style: `https://${BucketName}.s3.amazonaws.com/${Key}`

Note in the above exemplar URLs the region is not part of the domain name.

The documentation shows the region begin concatenated withe s3 as in:
-  `s3-${AWS::Region}`

And you may see the region used as a sub-domain in the domain name as in:
- `s3.${AWS::Region}`

S3 URLs that include the region in the domain name will not work consistently across all the regions. This was learned "the hard way" through testing in various regions.

The host-style S3 URL does involve a DNS name propagation latency.  That is not likely to be an issue, but it may be something to consider.

For consistency, we went with "path-style" URLs for all templates.
