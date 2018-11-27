# IBM Cloud Private AWS Deployment Automation Development and Test

This document is intended to capture the organization of the ICP AWS automation artifacts and the mechanics of the development and testing cycle.

The implementation details are described in [IBM Cloud Private Deployment Automation Implementation Details](implementation-details.md)

The automation to deploy an IBM Cloud Private cluster is complicated.  The automation is made up of several kinds of artifacts (in order of significance):
- CloudFormation templates
- Python scripts
- Ansible playbooks
- Bash scripts

All automation artifacts are maintained in a development git repository accessible only within IBM. Once deployment testing is complete, the automation artifacts used for the AWS QuickStart are copied to an AWS QuickStart git repository which is publicly accessible.  Additional testing is done using TaskCat and the AWS QuickStart git repository.

For details about testing with TaskCat see [Using TaskCat to deploy the IBM Cloud Private QuickStart](using-taskcat.md)   

## CloudFormation templates

The CloudFormation templates describe the networks and virtual machines that make up the ICP cluster.  

All of the CloudFormation templates are in YAML.  Early in the life of the project JSON was used, but the JSON templates became to unwieldy to read and edit.  YAML has its idiosyncrasies with respect to indentation and certain characters such as colon (:) that have syntactic meaning. However, YAML is easier to read and edit and is more syntactically compact than JSON.

The Atom editor is a good editor for working with the CloudFormation templates.  Atom is good for working with git repositories as well.  Any editor that supports YAML syntax and is designed to work with git repositories should work well.

Some of the CloudFormation templates define resources that are either an `AWS::EC2::Instance` or a `AWS::AutoScaling::LaunchConfiguration`.  Those types of resources have a `UserData` property that is bash shell scripting.

The `UserData` content is kept to a minimum to keep the amount of script editing that needs to be done in the template to a minimum. Because the template is fundamentally a YAML file, there is no editor syntax assistance for the `UserData` script content, which is at least one motivation to keep the `UserData` content to a minimum.

The primary role of the `UserData` script is to install software and kickoff the main scripting that runs on each virtual machine.

### CloudFormation parameter files

There are a number of sample parameter files in the `cloudformation/parameters` folder of the development git repository.

The CloudFormation parameter files must be in JSON.

The names of the parameter files reflect the region they are to be used in, whether the deployment is HA or non-HA, (the number of Availability Zones) and whose primary EC2 key-pair is configured for use.

When specifying parameters for a deployment in a specific AWS region, some things to keep in mind about AWS regions:
- Not all regions have 3 or more Availability Zones.
- Some Availability Zones within a region do not support the EC2 instance types permitted to be used for the ICP nodes.
- Some AWS regions may not support the protocol used by `cfn-init` to access the S3 buckets.  (The work-around for this issue is to use the S3 bucket in a neighboring region, e.g., when deploying ICP to `us-east-2` use the script bucket in `us-east-1` because `cfn-init` cannot access a `us-east-2` bucket.)
- An EC2 key-pair needs to be defined in each region (TBD - Need to confirm) 

## Python scripts

The Python scripts make up most of the scripted automation. AWS provides a complete Python library named `boto3` that can be used for interacting with all of the AWS services.

The Python scripts are developed using Eclipse and the PyDev plugin.

The Python scripts are divided into 3 projects:
- `aws-icp-bootstrap`: The Python automation that runs on the ICP Boot node. This collection of scripts is usually referred to as the bootstrap scripts.
- `aws-icp-nodeinit`: The Python automation that runs on each of the ICP cluster nodes. This collection of scripts is often referred to as the nodeinit scripts.
- `YAPythonLibrary`: A library of supporting modules that are used by the bootstrap and nodeinit scripts.

*TODO*: There are some additional projects that support unit testing and other basic capabilities.

The bootstrap and nodeinit projects each have an Ant script that does a "build" of the bootstrap and nodeinit "script package" artifacts that are ultimately used to "install" the scripts onto their respective nodes.

For the bootstrap project the Ant build script is named: `Build-AWS-ICP-Bootstrap-ZIP.xml`.

For the nodeinit project the Ant build script is named: `Build-AWS-ICP-NodeInit-ZIP.xml`

One of the properties in each of the build scripts is a `ScriptPackageVersion`. The version is tacked onto the root name of the zip archive. The version is also injected into the main Python module, i.e., `bootstrap.py` or `nodeinit.py`.

The Ant build scripts use a "staging area" in the local file system (defined by the `StagingAreaHome` property value) to build the script packages.  The script packages are then copied to S3 buckets into a directory that mimics the bucket structure expected by the QuickStart testing framework (TaskCat). The script packages are copied to S3 buckets in all regions listed in the `AWSRegions` property.

The developer can edit each of the Ant build scripts to define the following:
- `StagingAreaHome`
- `QuickStartBucketRootName`
- `AWSRegions`
