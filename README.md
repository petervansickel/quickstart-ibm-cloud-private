# Deploying IBM Cloud Private using AWS step-by-step

The following is a description of the steps to deploy IBM Cloud Private on AWS using the QuickStart deployment.

- Create an S3 bucket in the region where you want to deploy the ICP cluster.  This bucket is referred to as the `ICP Archive Bucket` and you will provide the name of that bucket in the `ICPArchiveBucketName` input parameter.
- Copy the Docker installation binary file, that comes with the version of ICP you are going to install, to the `ICP Archive Bucket` bucket.  The path to the Docker installation binary file is provided in the `DockerInstallBinaryPath` input parameter.
- Copy the ICP installation archive file to the `ICP Archive Bucket` bucket. The path to the ICP installation archive file is provided in the `ICPArchivePath` input parameter.

- The bootstrap and node initialization script packages and the CloudFormation templates also need to be available in an S3 bucket.  You can use either the `ICP Archive` S3 bucket or a different S3 bucket for the script packages.  The name of the script package S3 bucket is provided in the `ICPScriptBucketName`. We suggest you put the scripts in a `scripts` directory and the templates in a `templates` directory in the bucket.
- Copy the `aws-icp-bootstrap-v#.#.#.zip` into a scripts directory in the ICP script bucket.
- Copy the `aws-icp-nodeinit-v#.#.#.zip` into a scripts directory in the ICP script bucket.
- Copy the following templates to the ICP script bucket (into a `templates` directory):
  - 01-ibm-cloud-private-boot-###.yaml
  - 02-ibm-cloud-private-master-###.yaml
  - 03-ibm-cloud-private-mgmt-###.yaml
  - 05-ibm-cloud-private-proxy-###.yaml
  - 06-ibm-cloud-private-worker-###.yaml
  - 98-ibm-cloud-private-shared-storage-###.yaml
  - 99-ibm-cloud-private-iam-security-###.yaml

- Create an S3 bucket for a deployment log file repository.  The name of the log repository S3 bucket is provided in the `ICPDeploymentLogsBucketName` input parameter.

- Create a file with input parameter values.  See the section that describes the input parameters for information on each input parameter.

- Clone the git repository with the templates and other AWS QuickStart artifacts. *TODO:* Need more detail here.

- From a shell execute the command to kick off the root stack deployment:

*TODO:* Clean this up to reflect the actual AWS QuickStart git repo.
```
aws cloudformation create-stack --template-body file://~/git/aws-icp-quickstart/cloudformation/stacked/00-ibm-cloud-private-root-010.yaml --parameters file://~/git/aws-icp-quickstart/cloudformation/stacked/stacked-parameters-deploy-010.json --capabilities CAPABILITY_IAM --stack-name MyICPStack-2018-0901-04
```
The `stack-name` must be unique in the AWS region.

[ICP installation parameters](docs/input-parameters.md)

## Hostname mapping and Route53 DNS

This section documents the "tricks" that are used to get request traffic from a user's laptop routed properly to the ICP management console.

- In the laptop `/etc/hosts` file make an entry for `clustername.clusterdomain`.  
  - The default cluster name is `mycluster`.  
  - The default cluster domain is `icp`.  
  - The address for this entry would be the public IP address of the master node ELB.
  - The public IP address of the master node ELB can be determined using `nslookup` on the master node ELB host name that is listed in the outputs of the root stack template.

- A Route53 record is created by the CloudFormation template (the root template) that is an alias that maps the `ClusterCADomain` to the master node ELB public hostname.

## Sample command line invocations

As of 2018-0815:
```
aws cloudformation create-stack --template-body file://~/git/aws-icp-quickstart/cloudformation/stacked/ibm-cloud-private-root-010.yaml --parameters file://~/git/aws-icp-quickstart/cloudformation/stacked/stacked-parameters-pvsdeploy-010.json --capabilities CAPABILITY_IAM --stack-name pvsICPTestStack-2018-0815-01
```

# When things go wrong

This section captures common deployment problems and the solution.

## After deployment, cannot SSH to the boot node or any of the cluster nodes

Make sure your laptop IP address is within the inbound CIDR defined for `ExternalSSHSecurityGroup`.

Depending on your network provider, your IP address may change even though you did not disconnect from the network.

The `ExternalSSHSecurityGroup` inbound rules can be edited to allow your laptop to get in.

## After deployment, connection timeout to the ICP management console

You need to put an entry your laptop `/etc/hosts` file that maps the master node ELB public DNS name to `clustername.clusterdomain`, for example:
```
54.241.72.233      mycluster.icp
```

You also need to be sure the `ExternalICPAdminSecurityGroup` has an inbound rule that permits the IP address of your laptop to access the cluster on port 8443 (and port 8080 if you want to use that port).  

If the value of `ExternalICPAdminLocation` in the parameters that were provided to the deployment is not a CIDR that includes your laptop's IP address then you won't have access and the connection attempt to the ICP management console will time out.

The `ExternalICPAdminSecurityGroup` inbound rules can be edited to allow your laptop to get in.

## After deployment, a 500 server error is reported by the management console

You may see this problem when testing multiple ICP deployments.

**Solution:** Clear browser history, specifically cookies from interaction with an earlier deployment.

# Limitations

This section describes the limitations of the current release.

- Using ICP Community Edition is not currently supported.  Modifying the installation scripts to support ICP Community Edition installs, should be relatively straight-forward.  Using ICP CE has not been a focus of MVP1.

- The EC2 instances are all based on Ubuntu.  The UserData code is specific to Ubuntu package manager.  There may be other ubuntu specific implementation details.

- Bring your own PKI certificates is not currently supported. This would be relatively easy to support.  Need to add parameters to point to S3 bucket to get the certificates and copy them into the appropriate directory as part of the inception configuration script.

- *TBD*
