# ICP-AWSQuickStart
IBM Cloud Private assets for creating the AWS QuickStart

# The parameters
- VPCName
(optional) Name used in the tags of the VPC

- ResourceOwner
(required) AWS name captured in the `Owner` tag of all the resources defined in the VPC.

- KeyName
(required) Name of an existing EC2 key pair used to permit SSH login on the public IP of the deployed EC instances in the stack.

- ICPBucketName - The name of the S3 bucket that holds the ICP install artifacts.
- ICPArchivePath - The relative path to the ICP installation archive in the ICP bucket.
- DockerInstallBinaryPath - The relative path to the Docker install binary in the ICP bucket.
- ICPBootstrapBucketName - The name of the S3 bucket that holds the ICP bootstrap script package.
- ICPBootstrapScriptPackagePath - The relative path to the bootstrap script package in the bootstrap bucket.
- BootInstanceType - The EC2 instance type for the boot node.
- MasterInstanceType - The EC2 instance type for the master nodes.
- WorkerInstanceType - The EC2 instance type for the worker nodes.
- WorkerNodeCount - The number of worker nodes to deploy.  Defaults to 2.
- SSHLocation - The IP address range for systems to access the instances that get deployed.  For testing this is usually a single IP with a `/32` mask, e.g. `96.10.122.246/32`.  Your laptop IP address will change when you move from home to office, to airport, to motel, etc.


# Launching the various templates

```
aws cloudformation create-stack --template-body file://~/git/ICP-AWSQuickStart/baseICPStack.json --stack-name pvsICPQuickStartTest04 --parameters file://~/git/ICP-AWSQuickStart/parameters-pvsdeploy.json --capabilities CAPABILITY_IAM
```

- base-icp-stack-test
```
aws cloudformation create-stack --template-body file://~/git/ICP-AWSQuickStart/base-icp-stack-test.json --stack-name pvsICPQuickStartTest05 --parameters file://~/git/ICP-AWSQuickStart/parameters-pvsdeploy.json --capabilities CAPABILITY_IAM
```

- ssm-parameter-test-stack
```
aws cloudformation create-stack --template-body file://~/git/ICP-AWSQuickStart/ssm-parameter-test-stack.json --stack-name pvsICPQuickStartTest05 --parameters file://~/git/ICP-AWSQuickStart/parameters-pvsdeploy.json --capabilities CAPABILITY_IAM
```


# Parameter passing implementation

The nodes in a cluster need to be able to exchange some key pieces of information:
- Boot node needs to know the role and private IP address of each cluster member node
- Boot node needs the host RSA fingerprint of each cluster node to put in the SSH `known_hosts` file.
- Each cluster node needs the SSH public key of the boot node to put in the `authorized_keys` file in `~/.ssh`.

- Working through the details of using `AWS::SSM::Parameter` as a mechanism to exchange this information among the nodes of the ICP cluster.
- (As best I can tell) all of this needs to happen via the AWS CLI post-instantiation.

- The parameter names can be organized using paths using a file path syntax.
