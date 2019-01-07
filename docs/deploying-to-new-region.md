# Deploying IBM Cloud Private to a new AWS region

This document describes the steps to setting up a new AWS region for deployment of IBM Cloud Private.

The steps associated with setting up S3 buckets could be scripted.  (TODO - Develop a script to configure a region for ICP deployment using the AWS CloudFormation automation.)

# S3 Buckets

By convention we have been using the following different S3 buckets in each region that each play different role:
- Installation artifact bucket with a root name: `ibm-cloud-private`
- Script package bucket with a root name: `aws-icp-quickstart`
- Deployment logs bucket with a root name: `aws-icp-quickstart-logs`

## Installation artifacts bucket

- Create an S3 bucket for the region to hold the installation artifacts.
  - The root name of the bucket: `ibm-cloud-private`
  - The full bucket name: `ibm-cloud-private-<region>` where `<region>` is the AWS region name, e.g., `us-east-1`, `ap-northeast-2`.
  - For each supported ICP version, create appropriate version folders in the bucket, e.g., `3.1.0`, `3.1.1`

- For each supported ICP version, copy the ICP installation artifacts from the S3 bucket for some other region to the new bucket.  The AWS command line is the only way to do the copy.
  - Copy the ICP tarball:
  ```
  aws s3 cp s3://ibm-cloud-private-us-west-1/3.1.1/ibm-cloud-private-x86_64-3.1.1.tar.gz s3://ibm-cloud-private-ap-northeast-2/3.1.1/ibm-cloud-private-x86_64-3.1.1.tar.gz
  ```
  - Copy the Docker install archive:
  ```
  aws s3 cp s3://ibm-cloud-private-us-west-1/3.1.1/icp-docker-18.03.1_x86_64.bin s3://ibm-cloud-private-ap-northeast-2/3.1.1/icp-docker-18.03.1_x86_64.bin
  ```

- In the `aws-icp-bootstrap` project, in the `yaml` directory, modify the `icp-install-artifact-map.yaml` file to include the new region bucket name for the new region, e.g.,
```
s3-buckets:
  us-east-1: ibm-cloud-private-us-east-1
  us-east-2: ibm-cloud-private-us-east-2
  us-west-1: ibm-cloud-private-us-west-1
  ap-northeast-2: ibm-cloud-private-ap-northeast-2
```

- In the `aws-was-init` project, in the `yaml` directory, modify the `was-install-artifact-map.yaml` to include the new region bucket name for the new region.

## Script package bucket

Create an S3 bucket in the new region named: `aws-icp-quickstart-<region>` where `<region>` is the AWS region name, e.g., `us-east-1`, `ap-northeast-2`, etc.

By convention the root folder of the script package bucket is named `quickstart-ibm-cloud-private`.  This follows the AWS QuickStart convention for naming the root folder the same as the Git repository where the AWS QuickStart artifacts are stored.

Within the `quickstart-ibm-cloud-private` folder, the following folders are defined:
- `templates` (required) - where the CloudFormation templates are located
- `scripts` (required) - where the script packages are located
- `custom` (optional) - A place for deployment specific content
- `keys` (optional) - A place to put a file of SSH public keys to be included as `authorized_keys` on the ICP boot node.

At a minimum create the required folders.

## Logs bucket

Create an S3 bucket in the new region named: `aws-icp-quickstart-logs-<region>` where `<region>` is the AWS region name, e.g., `us-west-1`, `ap-northeast-2`, etc.

No special folders need to be created for the logs bucket.  

# Build automation script changes

This section covers changes that need to be made to various Ant build scripts that copy deployment automation artifacts to the S3 buckets in the regions.

- Update the `ExportTemplatesToS3.xml` Ant script to include the new region in the `AWSRegions` property value.
- Run the `ExportTemplatesToS3.xml` script to copy the desired templates to the new region.  In the sample here the `0.9.5` templates are copied to `ap-northeast-2`:
```
ant -buildfile ~/git/aws-icp-quickstart/cloudformation/ExportTemplatesToS3.xml -Dversion=0.9.5 -DAWSRegions="ap-northeast-2"
```
If the `AWSRegions` are not specified on the command line, then all the regions defined in the value for AWSRegions will get a copy of the templates for the given `version`.

- Update the following Ant build scripts to include the new region in the `AWSRegions` property value.
  - `Build-AWS-ICP-Bootstrap.xml`
  - `Build-AWS-ICP-NodeInit.xml`
  - `Build-AWS-WAS-Init.xml`

NOTE: If you don't intend to include a WAS node in the ICP deployment to support application migration activities then adding the region to the `Build-AWS-WAS-Init.xml` is not necessary.

- Run the script package build scripts to get the script package archive copied out to the new region bucket.

# CloudFormation templates

If the new region you are deploying to is not included in the `AWSRegionAMIEC2` mapping in the CloudFormation templates that deploy EC2 instances, then you will need to add the region and the AMI ID for the operating system images that you may want to use.

The templates with a `AWSRegionAMIEC2` mapping:
- `01-ibm-cloud-private-boot.yaml`
- `02-ibm-cloud-private-master.yaml`
- `03-ibm-cloud-private-mgmt.yaml`
- `04-ibm-cloud-private-va.yaml`
- `05-ibm-cloud-private-proxy.yaml`
- `06-ibm-cloud-private-worker.yaml`

In the mapping you will need to add lines similar to:
```
ap-northeast-2:
  Ubuntu16: ami-0eee4dcc71fced4cf
```

This URL provides a comprehensive table for Ubuntu AMIs by region: [Amazon EC2 AMI Locator](https://cloud-images.ubuntu.com/locator/ec2/)

After you make the changes to the templates be sure to copy them to the appropriate region bucket.  You can use the `ExportTemplatesToS3.xml` ant script to do so as described above.

# Deployment parameter files

The naming convention for the CloudFormation deployment parameter files includes a region name.  The usual approach is to make a duplicate of the deployment parameter file for one of the regions that has already been in use, change its name to use the new region name, then edit the region specific parameters.  For example, `icp310-paramaters-us-east-1-1az-nonha-pvsdeploy.json` gets duplicated to `icp310-paramaters-ap-northeast-2-1az-nonha-pvsdeploy.json`. Then the region specific parameters are modified:
- `AvailabilityZones`
- `ICPDeploymentLogsBucketName`
- `KeyName` (you need a deployer key in each region)
- `QSS3BucketName` (the script package bucket)

# Deploying from the command line

In order to deploy to the new region from the command line, you need to modify your AWS config to use the new region.

The simplest approach modifying the AWS CLI region is to edit the `~/.aws/config` file to change the region.

Or you can run the `aws configure` command to change the region.
