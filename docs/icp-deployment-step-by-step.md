# Deploying IBM Cloud Private on AWS step-by-step

The following is a description of the steps to deploy IBM Cloud Private on AWS using CloudFormation templates and Python scripts that provide a fully automated deployment.  

*NOTE:* This document **does not** describe the deployment process for the actual AWS QuickStart.  The AWS QuickStart for IBM Cloud Private is available on the AWS QuickStart home page. (TBD: Need URL)

These instructions are intended only for use within IBM.

# Pre-requisites summary

- Clone the git repository with the templates and script packages and other AWS QuickStart artifacts. *TODO:* Need more detail here.  Currently this git repository is at: https://github.ibm.com/pvs/aws-icp-quickstart

- In the region where you want to deploy ICP, there needs to be an S3 bucket named, `ibm-cloud-private-<region>`, where `<region>` is the region name, e.g., `us-east-1`, `us-west-2`, etc. In that bucket there needs to be a folder with the ICP version number, e.g., `3.1.0`, `3.1.1`, etc.  In the folder for a given ICP version must be the ICP installation tar-ball and the Docker installation binary. One of the steps in the installation process is to use a pre-signed URL to copy the installation artifacts from the appropriate S3 bucket key to the boot node.  All of the ICP cluster nodes copy the Docker installation binary to `/root/docker/icp-install-docker.bin`. The boot node orchestrates the installation of Docker on each cluster node.

- Also in the region where you want to deploy ICP, there needs to be an S3 bucket with the templates, script packages and other deployment artifacts.  The name of this S3 bucket is provided in the `QSS3BucketName` input parameter.  The folder structure of this bucket must be as follows:
  - top level folder (name provided in `QSS3KeyPrefix`)
    - `custom`
    - `keys`
    - `scripts`
    - `templates`

- An Ant script named `ExportTemplatesToS3.xml` is available in the `cloudformation` folder of the development git repository for copying the CloudFormation templates to the S3 bucket for templates.  The `version` property of the Ant script can be used to define which version to copy to S3. The `AWSRegions` property can be used to specify which AWS regions to copy the templates to. Sample invocation of the Ant script:
```
ant -buildfile ~/git/aws-icp-quickstart/cloudformation/ExportTemplatesToS3.xml -Dversion=0.9.5
```

The remainder of this document provides the details you need to execute a successful deployment.

# Detailed steps

- Create a file with input parameter values.  A complete description of the input parameters is available in [ICP installation parameters](input-parameters.md)  

CloudFormation parameter files must be in JSON format because they are passed directly to the CF engine in a REST call.

- From a shell execute the command to kick off the root stack deployment:
```
aws cloudformation create-stack --template-body file://~/git/aws-icp-quickstart/cloudformation/0.9.5/00-ibm-cloud-private-root.yaml --parameters file://~/git/aws-icp-quickstart/cloudformation/parameters/0.9.5/icp310-parameters-us-east-1-3az-ha-pvsdeploy.json --capabilities CAPABILITY_IAM --stack-name pvsICPTestStack-2018-1126-02
```
The `stack-name` must be unique in the AWS region.  The stack naming convention above includes a year and date and a deployment number to ensure uniqueness.

## Hostname mapping and Route53 DNS

This section documents the "tricks" that are used to get request traffic from a user's laptop routed properly to the ICP management console.

- In the laptop `/etc/hosts` file make an entry for `ClusterName.VPCDomain`.  
  - The default cluster name is `mycluster`.  
  - The default VPC domain is `example.com`.  
  - The address for this entry would be the public IP address of the master node ELB.
  - The public IP address of the master node ELB can be determined using `nslookup` on the master node ELB host name that is listed in the outputs of the root stack template.

- A Route53 record is created by the CloudFormation template (the root template) that is an alias that maps the `ClusterCADomain` to the master node ELB public hostname.

## Sample command line invocations

**IBM Internal Use Only**

The command samples assume the AWS ICP QuickStart git repo is cloned to the deployer's desktop.  

The parameter JSON files are wired for S3 buckets that are accessible by IBM AWS account owners using the Hursley Lab account ID.  

S3 buckets have set up in `us-west-1`, `us-east-1` and `us-east-2` for the artifacts that are needed for the installation.

As of 2018-1127:

```
aws cloudformation create-stack --template-body file://~/git/aws-icp-quickstart/cloudformation/0.9.5/00-ibm-cloud-private-root.yaml --parameters file://~/git/aws-icp-quickstart/cloudformation/parameters/0.9.5/icp310-parameters-us-east-1-3az-ha-pvsdeploy.json --capabilities CAPABILITY_IAM --stack-name pvsICPTestStack-2018-1126-02
```
