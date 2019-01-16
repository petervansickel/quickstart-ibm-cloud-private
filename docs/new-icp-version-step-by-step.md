# New ICP release

This document describes the steps to take to incorporate a new ICP release into the QuickStart framework.

A new ICP release may introduce new features that are not supported by the current scripting or CloudFormation templates. For example there may be new configuration information in `config.yaml` that is not supported.

1. Create a new version folder in all of the S3 buckets in all regions where the ICP deployment is supported.  The S3 bucket names are of the form: `ibm-cloud-private-<region>` where `<region>` is the AWS region identifier, e.g., `us-east-1`, `us-west-1`, etc.  

2. Copy the new ICP install image and Docker install binary to each S3 bucket into the new version folder.

3. In the bootstrap script package under the `config` directory, create a `config.yaml` template with the version included in the file name.  If the `config.yaml` template has support for new features there may need to be changes made to the bootstrap script to support those new features.  Otherwise, a copy of the previous `config.yaml` template should be sufficient.

4. In the bootstrap script package under the `yaml` directory, modify the `icp-install-artifact-map.yaml` to include a stanza for the new version.

5. Rebuild the `bootstrap` script package to include the new coniguration template and installation artifact map in the build.  The Ant build script has a deployment task that copies the new script package archive to buckets in all of the regions where ICP deployment is supported.

6. Rebuild the `nodeinit` script package to include the new installation artifact map in the build. The cluster nodes install Docker and they will need to see the updates to the install map to get the Docker install binary for the new release. The Ant build script has a deployment task that copies the new script package archive to buckets in all of the regions where ICP deployment is supported.

7. Create a new version directory in every S3 bucket in every region where ICP may be deployed.  Copy the ICP installation tar ball to the version directory in every region.  Copy the Docker binary to the version directory in every region.

8. Change the input parameters to use a new value for ICPVersion.  
