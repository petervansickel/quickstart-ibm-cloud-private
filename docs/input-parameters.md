# ICP installation parameters

The installation parameters in alphabetical order are described below.  The "source of truth" for all instance parameters is the root template.  

- ApplicationDomains
  - A list of fully qualified domain names used for applications.  Each name gets an alias record in the Route53 DNS to the Proxy node Elastic Load Balancer public DNS name. The ApplicationDomains must be consistent with the VPCDomain.  NOTE: Currently only a single ApplicationDomain is supported.
  - Default: `myapp.example.com`

- ApplicationStorageMountPoint
  - Mount point for the EFS volume to be used for application shared storage. The Kubernetes EFS provisioner uses this mount point.
  - Default: `/mnt/storage`

- AvailabilityZoneCount
  - The number of availability zones to be used for the deployment. Keep in mind that some regions may be limited to 2 availability zones.  For a single ICP cluster to be highly available, 3 availability zones are needed to avoid a single point of failure when using 3, 5 or 7 master nodes or etcd nodes.  With less than 3 availability zones, one of the AZs will have more master nodes (or etcd nodes) than can be lost without losing a majority of the etcd instances.
  - Default: 1
  - Allowed values: 1, 3

- AvailabilityZones
  - List of Availability Zones to use for the subnets in the VPC. To get the names of Availability Zones available to you using the AWS CLI: aws ec2 describe-availability-zones

- BootNodeInstanceType:
  - The EC2 instance type to use for the boot node.  The boot node is dedicated to the orchestration of the ICP deployment.
  - Default: `m5.xlarge`

- CFNTemplateVersion
  - The Cloud Formation template version to use for the deployment.  The version string provided is used to determine the S3 path for the templates in the ICP script bucket (ICPScriptBucketName) templates folder.

- ClusterCADomain
  - The fully qualified domain name (host name) to use for the `cluster_CA_domain` attribute in the `config.yaml` ICP configuration file.  For a production deployment this parameter should be provided.  It must be the name used in the CN attribute of the PKI certificates used by the cluster for administrative access to the cluster.
  - Default: `mycluster.example.com`

- ClusterCIDR (**required**)
  - The CIDR for the ICP cluster overlay network.  This gets assigned to the `network_cidr` attribute in `config.yaml`.  The value provided must be a network that does not conflict with the AWS VPC network defined for the `ClusterSubnetCidr`.  It also must not conflict with the ICP service overlay network defined by the `ServiceCIDR`.
  - Must be a valid IP CIDR range of the form x.x.x.x/x.
  - Default: 192.168.0.0/16

- ClusterDomain
  - The network domain of the ICP cluster overlay network. WARNING: Due to a defect in ICP 3.1.0 the ClusterDomain value must be `cluster.local`.  When the ClusterDomain is some other value, MongoDB fails to start.  The defect will be corrected in the next fixpack release.  
  - Default: `cluster.local`

- ClusterLBAddress
  -  The value to use for the cluster load balancer address.  This value is used to drive the logic in the bootstrap script.
  - AllowedValues:
    - `UseMasterELBAddress`
    - `UseMasterELBName`
    - `UseClusterName`
  - Default: `UseClusterName`

- ClusterName
  - The name of the cluster.
  - Default: `mycluster`

- ClusterPKIBucketName
  - The S3 bucket where the cluster PKI artifacts are located. If not provided, self-signed PKI artifacts will be created and used.
  - Default: ''

- ClusterPKIRootPath:
  - The path in the cluster PKI S3 bucket where the user defined PKI key and certificate files are found.  This is the key and certificate that used for the master node identity.  The CN of the key and certificate must be the same value that is provided in ClusterCADomain. The extensions on the root path are assumed to be .key and .crt to get the key and certificate files respectively. DO NOT provide a leading / on the path value. If not provided, self-signed PKI artifacts will be created and used.
  - Default: ''

- CustomArtifactsPath:
  - Path to zip archive in the ICP script bucket (ICPScriptBucketName) for an archive of additional artifacts, typically scripts, for ICP cluster administration extracted on the boot node in the root home directory. (Optional)
  - Default: ''

- DockerInstallBinaryPath (**required**)
  - The path to the Docker install binary in the ICP archive bucket (ICPArchiveBucketName).

- ExcludedMgmtServices
  - Comma separated list of management services to be excluded from the IBM Cloud Private deployment.  Services that may be excluded are: `service-catalog`, `metering`, `monitoring`, `istio`, `vulnerability-advisor`, `custom-metrics-adapter`
  - Default: "`istio`,`vulnerability-advisor`,`custom-metrics-adapter`"

- ExternalApplicationLocation
  - The IP address CIDR that can be used to get to ICP Proxy ELB for access to deployed workloads on the ICP worker nodes from the external network. NOTE: Currently, this parameter is not implemented.
  - Default: `0.0.0.0/0`

- ExternalICPAdminLocation
  - The IP address range that can be used to get to ICP Master ELB from the external network.
  - Default: `0.0.0.0/0`

- ExternalSSHLocation (**required**)
  - The IP address range that can be used to SSH to the boot node.

- FixpackFileName:
  - The name of the fixpack file, e.g., `ibm-cloud-private-2.1.0.3-fp1.sh`. Do not include a leading / on the path value.
  - Default: ``

- FixpackInceptionImageName
  - The name of the inception image used for the ICP installation when the ICP fixpack is to be installed, e.g., `ibmcom/icp-inception:2.1.0.3-ee-fp1`

- FixpackIntallCommandString:
  - The command string used to install the ICP fixpack, if any.  The command string would likely need to be provided as it may be different for each fix pack.  The fixpack documentation will have the command string used to install the fixpack.
  - Default: `install -v`

- ICPArchiveBucketName (**requred**)
  - The name of the S3 bucket where the ICP install archive and Docker install binary is located.

- ICPArchivePath (**required**)
  - The path to the ICP install archive in the ICP bucket. Do not include a leading / on the path value.

- ICPBootNodeScriptPackagePath (**required**)
  - The path in the S3 bucket to the ICP Boot node script package (zip) file. Do not include a leading / on the path value.

- ICPClusterNodeScriptPackagePath (**required**)
  - The path in the S3 script bucket to the ICP cluster node script package (zip) file. Do not include a leading / on the path value. Cluster nodes are master, proxy, worker, management, vulnerability advisor.

- ICPDeploymentLogsBucketName (**required**)
  - The name of the S3 bucket where ICP stack deployment logs are to be exported. The deployment logs provide a record of the boot strap scripting actions and are useful for problem determination if the deployment fails in some way.

- ICPScriptBucketName (**required**)
  - The name of the S3 bucket where the ICP boostrap and node initialization script packages are located. The script bucket name and the path to the script packages are combined to download the script packages to the boot node and the various cluster nodes.  The `ICP Script Bucket ` can be the same bucket as the `ICP Archive Bucket`.  It is recommended that scripts, templates and other installation artifacts be organized in folders within the bucket.

- ICPVersion (**required**)
  - The version of ICP to be deployed.  The full version must be provided, e.g., 2.1.0.3, 3.1.0.

- InceptionImageName (**required**)
  - The full name of the inception image to use for the ICP installation.

- InceptionInstallCommandString
  - The command string to use when invoking the ICP installation.
  - Default: `install -v`

- InceptionTimeout
  - The number of seconds to wait for the IBM Cloud Private inception container to complete the installation.  For a small HA cluster (12 nodes) with ICP images pre-installed locally (on each node), or with ICP images pulled from a private registry, and on disks with 8000 IOPS, the inception container typically completes the installation in about 60 minutes.
  - Default: `7200`

- InstallFromConfigSet
  - Variable used to determine when the installation images get copied to the ICP boot node.  If 'Yes', then the installation images are copied at the time the ICP boot node is instantiated using the BaseInstall config set defined in the instance.  If 'No', then the installation images are copied to the boot node using a pre-signed S3 URL as part of the bootstrap script.
  - AllowedValues
    - Yes
    - No
  - Default: No

- InstallICPFixpack
  - Indicate yes to install an ICP fixpack.  Indicate no if there is no fixpack to install or the fixpack installation is to be skipped.
  - AllowedValues
    - Yes
    - No
  - Default: No

- KeyFilePath
  - Path to a file in the ICP script bucket (ICPScriptBuckeName) with public keys for administrators who need SSH access to the boot node. (Optional)
  - Default: ''

- KeyName (**required**)
  - Name of an existing EC2 KeyPair to enable SSH access to the instance
  - Must be the name of an existing EC2 KeyPair.

- ManagementNodeCount:
  - Number of Management nodes to be deployed in the ICP cluster. For a dev deployment 1 is sufficient. For production deployments, at least 2 and typically 3 are deployed.  The management nodes run the resource and log monitoring monitoring components, e.g., Prometheus, Grafana and the ELK stack.
  - Default: 1

- ManagementNodeInstanceType
  - ICP management node AWS EC2 instance type
  - Default: `m5.2xlarge`

- MasterNodeCount
  -  Number of master nodes to be deployed in the ICP cluster. Must be an odd number. For a development deployment 1 is sufficient; for production deployments, 3.
  - Default: 1

- MasterNodeInstanceType
  - ICP master node AWS EC2 instance type.
  - Default: `m5.2xlarge`

- PrivateSubnetCIDR:
  - The CIDR block to be used for the private subnets.
  - Default: 10.10.10.0/20

- PrivateSubnets:
  - A list of CIDR blocks to be used for the private subnets defined in 1 or 3 Availability Zones.  If there is only 1 Availability Zone, then the subnet can be the same as the PrivateSubnetCIDR.  The private subnets cannot overlap and must be within the PrivateSubnetCIDR. Sample for 3 AZs: 10.10.10.0/24, 10.10.11.0/24, 10.10.12.0/24
  - Default: 10.10.10.0/24

- ProxyLBAddress:
  - The value to use for the proxy load balancer address.  This value is used to drive the logic in the bootstrap script.
  - AllowedValues:
    - UseProxyELBAddress
    - UseProxyELBName
    - UsePrimaryAppDomain
  - Default: 'UsePrimaryAppDomain'

- ProxyNodeCount
  - Number of Proxy nodes to be deployed in the ICP cluster. For a dev deployment 1 is sufficient. For production deployments, at least 2 and typically 3 are deployed.
  - Default: 1

- ProxyNodeInstanceType
  - ICP Proxy node AWS EC2 instance type
  - Default: `m5.xlarge`

- PublicSubnetCIDR
  - CIDR block used for the public subnets.  The PublicSubnetCIDR is used for defining public subnet security groups.  The PublicSubnetCIDR must be within the network defined by the VPCCIDR and not overlap with the PrivateSubnetCIDR.
  - Default: 10.10.20.0/22

- PublicSubnets
  - List of CIDRs to be used for 1 or more public subnets of the VPC. The number of CIDRs provided must equal the number of Availability Zones (AvailabilityZoneCount). The public subnets must be within the network defined by the PublicSubnetCIDR.  NOTE: CommaDelimitedList is invalid to pass into child templates.  Type is declared String, but it is intended to be a comma delimited list.  Sample for 3 AZs: 10.10.20.0/24, 10.10.21.0/24, 10.10.22.0/24
  - Default: 10.10.20.0/24

- ResourceOwner (**required**)
  - Value for the owner tag for the deployed resources associated with the stacks that get deployed.

- S3ICPFixpackExecutablePath
  - The S3 path to the latest ICP fixpack executable (.sh) file.
  - Default: ''

- S3ICPInceptionFixpackPath
  - The S3 path to the latest ICP inception fixpack archive (.tar) file.
  - Default: ''

- ServiceCIDR (**required**)
  - The CIDR for the ICP service overlay network.  This gets assigned to the `service_cluster_ip_range` attribute in `config.yaml`.  The value provided must be a network that does not conflict with the AWS VPC network.  It also must not conflict with the ICP cluster overlay network.
  - Default: `172.16.0.0/24`

- VPCCIDR
  - The VPC CIDR block. Must be in the form x.x.x.x/16-28.  This is the CIDR for the "underlay" network provided by AWS.
  - Default: `10.10.0.0/16`

- VPCDomain:
  - The network domain of the VPC.  The VPCDomain is used when defining the hosted zone.
  - Default: `example.com`

- VPCName
  - The name of the deployed Virtual Private Cloud
  - Default: `IBMCloudPrivateVPC`

- VulnerabilityAdvisorNodeCount
  - Number of Vulnerability Advisor nodes to be deployed in the ICP cluster. Not typically deployed for a development environment. For production deployments, at least 2 and typically 3 are deployed.  The VA nodes run the resource image and container security scanning components.
  - Default: 1

- WorkerNodeCount
  - Number of worker nodes (desired capacity) to be deployed in the ICP cluster.
  - Default: 2

- VulnerabilityAdvisorNodeInstanceType
  - ICP Vulnerability Advisor node AWS EC2 instance type
  - Default: `m5.2xlarge`

- WorkerNodeInstanceType
  - ICP Worker node AWS EC2 instance type
  - Default: `m5.xlarge`
