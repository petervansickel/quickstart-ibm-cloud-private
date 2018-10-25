# Deploying IBM Cloud Private on AWS step-by-step

The following is a description of the steps to deploy IBM Cloud Private on AWS using the QuickStart deployment.

Summary of the what needs to be done without the details:
- Create one or two S3 buckets where installation artifacts are stored.  Create an S3 bucket for log archives.
- Clone the git repository that holds the CloudFormation templates and the installation script packages.
- Copy the ICP installation archives, the CloudFormation templates and installation script packages to the S3 buckets.
- Configure a file of CloudFormation input parameters that drive the installation process and provide the information needed to configure the IBM Cloud Private cluster.
- Kick off the installation.

The remainder of this document provides the details you need to execute a successful deployment.

- Clone the git repository with the templates and script packages and other AWS QuickStart artifacts. *TODO:* Need more detail here.  (Currently this git repository is at: https://github.ibm.com/pvs/aws-icp-quickstart  You need to contact Peter Van Sickel to get access if you don't have access.  In the near future this should be something publicly available.)

- Create an S3 bucket in the region where you want to deploy the ICP cluster.  This bucket is referred to as the `ICP Archive Bucket` and you will provide the name of that bucket in the `ICPArchiveBucketName` input parameter.
- Copy the Docker installation binary file, that comes with the version of ICP you are going to install, to the `ICP Archive Bucket` bucket.  The path to the Docker installation binary file is provided in the `DockerInstallBinaryPath` input parameter.
- Copy the ICP installation archive file to the `ICP Archive Bucket` bucket. The path to the ICP installation archive file is provided in the `ICPArchivePath` input parameter.

- The bootstrap and node initialization script packages and the CloudFormation templates also need to be available in an S3 bucket.  You can use either the `ICP Archive` S3 bucket or a different S3 bucket for the templates script packages.  The name of the script package S3 bucket is provided in the `ICPScriptBucketName`. We suggest you put the scripts in a `scripts` directory and the templates in a `templates` directory in the bucket.
- The script packages are available in the `script-packages` directory of the git repository.  The templates are available in the `cloudformation/stacked` directory of the git repository.  (*TBD:* The directory structure of the git repo will likely change once the artifacts are moved to the AWS Quickstart git repo.)
- Copy the `aws-icp-bootstrap-v#.#.#.zip` into a `scripts` directory in the ICP script bucket.
- Copy the `aws-icp-nodeinit-v#.#.#.zip` into a `scripts` directory in the ICP script bucket.
- Copy the following templates to the ICP script bucket (into a `templates` directory):
  - 01-ibm-cloud-private-boot-###.yaml
  - 02-ibm-cloud-private-master-###.yaml
  - 03-ibm-cloud-private-mgmt-###.yaml
  - 05-ibm-cloud-private-proxy-###.yaml
  - 06-ibm-cloud-private-worker-###.yaml
  - 98-ibm-cloud-private-shared-storage-###.yaml
  - 99-ibm-cloud-private-iam-security-###.yaml

- Create an S3 bucket for a deployment log file repository.  The name of the log repository S3 bucket is provided in the `ICPDeploymentLogsBucketName` input parameter.

- Create a file with input parameter values.  A complete description of the input parameters is available in [ICP installation parameters](input-parameters.md) A sample input file that you can get started with is provided in `stacked-parameters-sample-###.json`.  (CloudFormation parameter files must be in JSON format because they are passed directly to the CF engine in a REST call.) There are some dummy values in the sample parameters that are delimited by the `@` character and start with `YOUR`, e.g., `@YOUR_ADDRESS_CIDR@`, `@YOUR_AWS_ID@`, etc.  Other values in the sample may not be relevant depending on the version of ICP to be installed and whether or not a fixpack is to be installed.

- From a shell execute the command to kick off the root stack deployment:
```
aws cloudformation create-stack --template-body file://~/git/aws-icp-quickstart/cloudformation/stacked/00-ibm-cloud-private-root-010.yaml --parameters file://~/git/aws-icp-quickstart/cloudformation/stacked/stacked-parameters-deploy-010.json --capabilities CAPABILITY_IAM --stack-name MyICPStack-2018-0901-01
```
The `stack-name` must be unique in the AWS region.  The stack naming convention above includes a year and date and a deployment number to ensure uniqueness.

*TODO:* The above will need to change to reflect the actual AWS QuickStart git repo.

## Hostname mapping and Route53 DNS

This section documents the "tricks" that are used to get request traffic from a user's laptop routed properly to the ICP management console.

- In the laptop `/etc/hosts` file make an entry for `clustername.clusterdomain`.  
  - The default cluster name is `mycluster`.  
  - The default cluster domain is `icp`.  
  - The address for this entry would be the public IP address of the master node ELB.
  - The public IP address of the master node ELB can be determined using `nslookup` on the master node ELB host name that is listed in the outputs of the root stack template.

- A Route53 record is created by the CloudFormation template (the root template) that is an alias that maps the `ClusterCADomain` to the master node ELB public hostname.

## Sample command line invocations

**IBM Internal Use Only**

The command samples assume the AWS ICP QuickStart git repo is cloned to the deployer's desktop.  

The parameter JSON files are wired for S3 buckets that are accessible by IBM AWS account owners using the Hursley Lab account ID.  

S3 buckets have set up in `us-west-1`, `us-east-1` and `us-east-2` for the artifacts that are needed for the installation.

As of 2018-1024:

```
aws cloudformation create-stack --template-body file://~/git/aws-icp-quickstart/cloudformation/0.9.3/00-ibm-cloud-private-root.yaml --parameters file://~/git/aws-icp-quickstart/cloudformation/parameters/0.9.3/icp310-parameters-us-west-1-1az-nonha-pvsdeploy.json --capabilities CAPABILITY_IAM --stack-name pvsICPTestStack-2018-1024-01
```
