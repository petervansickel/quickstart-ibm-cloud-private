# ICP installation parameters

The installation parameters in alphabetical order are described below.

- BootNodeInstanceType:
  - The EC2 instance type to use for the boot node.  The boot node is dedicated to the orchestration of the ICP deployment.
  - Default: `m5d.xlarge`

- ClusterCADomain
  - The fully qualified domain name (host name) to use for the `cluster_CA_domain` attribute in the `config.yaml` ICP configuration file.  For a production deployment this parameter should be provided.
  - Default: The cluster name concatenated with `.icp`, for example, using the default cluster name: `mycluster.icp`

- ClusterCIDR (**required**)
  - The CIDR for the ICP cluster overlay network.  This gets assigned to the `network_cidr` attribute in `config.yaml`.  The value provided must be a network that does not conflict with the AWS VPC network defined for the `ClusterSubnetCidr`.  It also must not conflict with the ICP service overlay network defined by the `ServiceCIDR`.
  - Must be a valid IP CIDR range of the form x.x.x.x/x.

- ClusterDomain
  - The network domain of the cluster.
  - Default: `icp.local`

- ClusterName
  - The name of the cluster.
  - Default: `mycluster`

- ClusterVPCSubnetCidr (**required**)
  - The CIDR for the ICP cluster (physical/underlay) subnet.
  - Must be a valid IP CIDR range of the form x.x.x.x/x.

- DockerInstallBinaryPath (**required**)
  - The path in the S3 ICP Install Archive bucket to the Docker installation binary.

- ExcludedMgmtServices
  - Comma separated list of management services to be excluded from the IBM Cloud Private deployment.  Services that may be excluded are: `service-catalog`, `metering`, `monitoring`, `istio`, `vulnerability-advisor`, `custom-metrics-adapter`
  - Default: "`istio`,`vulnerability-advisor`,`custom-metrics-adapter`"

- ExternalApplicationLocation: (**required**)
  - The CIDR that defines the range of IP addresses permitted to access the ICP applications exposed through the ICP Proxy node Elastic Load Balancer and the ICP Proxy nodes.  (For test deployments this may be the IP address of a tester's laptop and it would be a /32 CIDR.  The IP address of your laptop is available from `myipaddress`.)

- ExternalICPAdminLocation (**required**)
  - The CIDR that defines the range of IP addresses permitted to access the ICP management console and management applications exposed through the ICP Master node Elastic Load Balancer and the Master nodes. (For test deployments this may be the IP address of a tester's laptop and it would be a /32 CIDR.  The IP address of your laptop is available from `myipaddress`.)

- ExternalSSHLocation (**required**)
  - The CIDR that defines the range of IP addresses permitted to access the ICP boot node and cluster node using SSH. (For test deployments this may be the IP address of a tester's laptop and it would be a /32 CIDR.  The IP address of your laptop is available from `myipaddress`.)

- FixpackFileName:
  - The name of the fixpack file, e.g., `ibm-cloud-private-2.1.0.3-fp1.sh`. Do not include a leading / on the path value.
  - Default: ``

- FixpackInceptionImageName
  - The name of the inception image used for the ICP installation when the ICP fixpack is to be installed.
  - Default: `ibmcom/icp-inception:2.1.0.3-ee-fp1`

- FixpackIntallCommandString:
  - The command string used to install the ICP fixpack, if any.  The command string would likely need to be provided as it will be different for each fix pack, e.g., `./cluster/ibm-cloud-private-2.1.0.3-fp1.sh`.  The fixpack documentation will have the command string used to install the fixpack.
  - Default: `install -v`

- ICPArchiveBucketName (**requred**)
  - The name of the S3 bucket where the ICP install archive and Docker install binary is located.

- ICPArchivePath (**required**)
  - The path to the ICP install archive in the ICP bucket. Do not include a leading / on the path value.

- ICPBootNodeScriptPackagePath (**required**)
  - The path in the S3 bucket to the ICP Boot node script package (zip) file. Do not include a leading / on the path value.

- ICPBootNodeTemplatePath (**required**)
  - The path in the S3 script bucket for the ICP Boot node CloudFormation template. Do not include a leading / on the path value. The root template uses the boot node nested stack template found here.
  - *TODO:* This can likely take a default.  We would need to require that the template path be in a particular place such as a templates directory.

- ICPClusterNodeScriptPackagePath (**required**)
  - The path in the S3 script bucket to the ICP cluster node script package (zip) file. Do not include a leading / on the path value. Cluster nodes are master, proxy, worker, management, vulnerability advisor.

- ICPDeploymentLogsBucketName (**required**)
  - The name of the S3 bucket where ICP stack deployment logs are to be exported. The deployment logs provide a record of the boot strap scripting actions and are useful for problem determination if the deployment fails in some way.

- ICPIAMTemplatePath (**required**)
  - The path in the S3 script bucket for the IAM CloudFormation template where roles and profiles are defined. Do not include a leading / on the path value. The root template uses the IAM template found here.

- ICPManagementNodeTemplatePath (**required**)
  -  The path in the S3 script bucket for the ICP Management node CloudFormation template. Do not include a leading / on the path value. The root template uses the master node stack template found here.
  - *TODO:* This can likely take a default.  We would need to require that the template path be in a particular place such as a templates directory.

- ICPMasterNodeTemplatePath (**required**)
  -  The path in the S3 script bucket for the ICP Master node CloudFormation template. Do not include a leading / on the path value. The root template uses the master node stack template found here.
  - *TODO:* This can likely take a default.  We would need to require that the template path be in a particular place such as a templates directory.

- ICPProxyNodeTemplatePath (**required**)
  -  The path in the S3 script bucket for the ICP Proxy node CloudFormation template. Do not include a leading / on the path value. The root template uses the master node stack template found here.
  - *TODO:* This can likely take a default.  We would need to require that the template path be in a particular place such as a templates directory.

- ICPScriptBucketName (**required**)
  - The name of the S3 bucket where the ICP boostrap and node initialization script packages are located. The script bucket name and the path to the script packages are combined to download the script packages to the boot node and the various cluster nodes.  The `ICP Script Bucket ` can be the same bucket as the `ICP Archive Bucket`.  It is recommended that scripts, templates and other installation artifacts be organized in folders within the bucket.

- ICPVersion (**required**)
  - The version of ICP to be deployed.
  - *TODO*: The version can be derived from the inception image name.

- ICPWorkerNodeTemplatePath (**required**)
  -  The path in the S3 script bucket for the ICP Worker node CloudFormation template. Do not include a leading / on the path value. The root template uses the master node stack template found here.
  - *TODO:* This can likely take a default.  We would need to require that the template path be in a particular place such as a templates directory.

- InceptionImageName (**required**)
  - The full name of the inception image to use for the ICP installation.

- InceptionInstallCommandString
  - The command string to use when invoking the ICP installation.
  - Default: `install -v`

- InceptionTimeout
  - The number of seconds to wait for the IBM Cloud Private inception container to complete the installation.  For a small HA cluster (12 nodes) with ICP images pre-installed locally (on each node), or with ICP images pulled from a private registry, and on disks with 8000 IOPS, the inception container typically completes the installation in about 30 minutes. YMMV
  - Default: `7200`

- InstallICPFixpack
  - Indicate yes to install an ICP fixpack.  Indicate no if there is no fixpack to install or the fixpack installation is to be skipped.
  - Permitted values are `True`, `False`, `Yes` or `No`.
  - Default: `No`

- KeyName (**required**)
  - Name of an existing EC2 KeyPair to enable SSH access to the instance
  - Must be the name of an existing EC2 KeyPair.

- LoadICPImagesLocally:
  - When true, load the IBM Cloud Private images into the local Docker registry on each node using an archive extraction command run directly on each node.  When false, load the ICP images using an Ansible playbook launched from the Boot node. This variable is used for experiments in comparing different installation techniques.
  - Permitted values are `True`, `False`, `Yes` or `No`
  - Default: `Yes`

- ManagementNodeCount:
  - Number of Management nodes to be deployed in the ICP cluster. For a dev deployment 1 is sufficient. For production deployments, at least 2 and typically 3 are deployed.  The management nodes run the resource and log monitoring monitoring components, e.g., Prometheus, Grafana and the ELK stack.
  - Default: 1

- ManagementNodeInstanceType
  - ICP management node AWS EC2 instance type
  - Default: `m5d.2xlarge`

- MasterNodeCount
  - Number of Master nodes to be deployed in the ICP cluster. Must be an odd number. For a development deployment 1 is sufficient. For production deployments typically 3 or 5.
  - Default: 1

- MasterNodeInstanceType
  - ICP master node AWS EC2 instance type.
  - Default: `m5d.2xlarge`

- ProxyNodeCount
  - Number of Proxy nodes to be deployed in the ICP cluster. For a dev deployment 1 is sufficient. For production deployments, at least 2 and typically 3 are deployed.
  - Default: 1

- ProxyNodeInstanceType
  - ICP Proxy node AWS EC2 instance type
  - Default: `m5d.xlarge`

- ResourceOwner (**required**)
  - Value for the owner tag for the deployed resources associated with the stacks that get deployed.

- S3ICPFixpackExecutablePath
  - The S3 path to the latest ICP fixpack executable (.sh) file.
  - Default: ''

- S3ICPInceptionFixpackPath
  - The S3 path to the latest ICP inception fixpack archive (.tar) file.
  - Default: ''

- ServiceCIDR (**required**)
  - The CIDR for the ICP service overlay network.  This gets assigned to the `service_cluster_ip_range` attribute in `config.yaml`.  The value provided must be a network that does not conflict with the AWS VPC network defined by `ClusterVPCSubnetCidr`.  It also must not conflict with the ICP cluster overlay network defined by the `ClusterCIDR`.

- SharedStorageTemplatePath
  - The path in the S3 script bucket for the ICP shared storage CloudFormation template. Do not include a leading / on the path value. The root template uses the shared storage stack template found here.
  - *TODO:* This can likely take a default.  We would need to require that the template path be in a particular place such as a templates directory.

- VPCName
  - The name of the deployed Virtual Private Cloud
  - Default: `IBMCloudPrivateVPC`

- VulnerabilityAdvisorNodeCount
  - Number of Vulnerability Advisor nodes to be deployed in the ICP cluster. Not typically deployed for a development environment. For production deployments, at least 2 and typically 3 are deployed.  The VA nodes run the resource image and container security scanning components.
  - Default: 1

- VulnerabilityAdvisorNodeInstanceType
  - ICP Vulnerability Advisor node AWS EC2 instance type
  - Default: `m5d.2xlarge`

- WorkerNodeInstanceType
  - ICP Worker node AWS EC2 instance type
  - Default: `m5d.xlarge`

- WorkerNodeCount
  - Number of worker nodes (desired capacity) to be deployed in the ICP cluster.
  - Default: 2
