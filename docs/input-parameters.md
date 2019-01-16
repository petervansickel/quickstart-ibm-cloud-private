# ICP installation parameters

The installation parameters in alphabetical order are described below.  The "source of truth" for all instance parameters is the root template.

In this document, the parameters with the notation (**required**) do not have a default value.  The deployer must provide a value.

- *[QS doc]* ApplicationDomains
  - A list of fully qualified domain names used for applications.  Each name gets an alias record in the Route53 DNS to the Proxy node Elastic Load Balancer public DNS name. The ApplicationDomains must be consistent with the VPCDomain.  NOTE: Currently only a single ApplicationDomain is supported.
  - Default: `myapps.example.com`

- *[QS doc]* ApplicationStorageMountPoint
  - Mount point for the EFS volume to be used for application shared storage. The Kubernetes EFS provisioner uses this mount point.
  - Default: `/mnt/storage`

- *[QS doc]* AvailabilityZoneCount
  - The number of availability zones to be used for the deployment. Keep in mind that some regions may be limited to 2 availability zones.  For a single ICP cluster to be highly available, 3 availability zones are needed to avoid a single point of failure when using 3, 5 or 7 master nodes or etcd nodes.  With less than 3 availability zones, one of the AZs will have more master nodes (or etcd nodes) than can be lost without losing a majority of the etcd instances.
  - Default: 1
  - Allowed values: 1, 3

- *[QS doc]* AvailabilityZones (**required**)
  - Comma delimited list (string) of Availability Zones to use for the subnets in the VPC. Be careful to choose availability zones that support the instance types of the ICP cluster members. To get the names of Availability Zones available to you using the AWS CLI: `aws ec2 describe-availability-zones`

- *[QS doc]* BootNodeInstanceType:
  - The EC2 instance type to use for the boot node.  The boot node is dedicated to the orchestration of the ICP deployment.
  - Default: `m5.xlarge`

- ClusterCADomain *[Deprecated]*
  - The fully qualified domain name (host name) to use for the `cluster_CA_domain` attribute in the `config.yaml` ICP configuration file.  For a production deployment this parameter should be provided.  It must be the name used in the CN attribute of the PKI certificates used by the cluster for administrative access to the cluster.
  - Default: `mycluster.example.com`

- *[QS doc]* ClusterCIDR
  - The CIDR for the ICP cluster overlay network.  This gets assigned to the `network_cidr` attribute in `config.yaml`.  The value provided must be a network that does not overlap with the AWS VPC network (`VPCCIDR`).  It also must not overlap with the ICP service overlay network defined by the `ServiceCIDR`.
  - Must be a valid IP CIDR range of the form x.x.x.x/x.
  - Default: 192.168.0.0/16

- *[QS doc]* ClusterDomain
  - The network domain of the ICP cluster overlay network. WARNING: Due to a defect in ICP 3.1.0 the `ClusterDomain` value must be `cluster.local`.  When the `ClusterDomain` is some other value, MongoDB fails to start.  The defect will be corrected in the next release.  
  - Default: `cluster.local`

- ClusterLBAddress
  -  The value to use for the cluster load balancer address.  This value is used to drive the logic in the bootstrap script.
  - AllowedValues:
    - `UseMasterELBAddress`
    - `UseMasterELBName`
    - `UseClusterName`
  - Default: `UseClusterName`

- *[QS doc]* ClusterName
  - The name of the cluster.
  - Default: `mycluster`

- *[QS doc]* ClusterPKIBucketName
  - The S3 bucket where the cluster PKI artifacts are located. If not provided, self-signed PKI artifacts will be created and used.
  - Default: ''

- *[QS doc]* ClusterPKIRootPath:
  - The path in the cluster PKI S3 bucket where the user-defined PKI key and certificate files are found.  This is the key and certificate that are used for the master node identity.  The CN of the key and certificate must be the same value that is provided in combination of the `ClusterName` and the `VPCDomain`. The extensions on the root path are assumed to be `.key` and `.crt` to get the key and certificate files respectively. **DO NOT** provide a leading / on the path value. If not provided, self-signed PKI artifacts will be created and used.
  - Default: ''

- *[QS doc]* CustomArtifactsPath:
  - Path to zip archive in the ICP script bucket (`QSS3BucketName`) for an archive of additional artifacts, typically scripts, for ICP cluster administration extracted on the boot node in the root home directory. (Optional)
  - Default: ''

- *[QS doc]* ExcludedMgmtServices
  - Comma separated list of management services to be excluded from the IBM Cloud Private deployment.  Services that may be excluded are: `service-catalog`, `metering`, `monitoring`, `istio`, `vulnerability-advisor`, `custom-metrics-adapter`
  - Default: "`istio`,`vulnerability-advisor`,`custom-metrics-adapter`"

- ExternalApplicationLocation
  - The IP address CIDR that can be used to get to ICP Proxy ELB for access to deployed workloads on the ICP worker nodes from the external network. NOTE: Currently, this parameter is not implemented.
  - Default: `0.0.0.0/0`

- ExternalICPAdminLocation
  - The IP address range that can be used to get to ICP Master ELB from the external network.
  - Default: `0.0.0.0/0`

- *[QS doc]* ExternalSSHLocation (**required**)
  - The network CIDR for IP addresses that can be used to SSH to the boot node. In single user test situations this can be a /32 CIDR.  Additional values can be added post-deployment from the AWS CloudFormation console.

- ICPArchiveBucketRootName
  - The root name of the S3 bucket where the ICP and Docker installation artifacts are located.  For the QuickStart this gets a default (required) value of `ibm-cloud-private`. The root name is used to form a full name that includes a dash (-), followed by the region name, e.g., `ibm-cloud-private-us-east-1`.  A bucket in each region is needed for efficiency of downloading the ICP installation artifacts to the deployed EC2 instances. The bucket name is needed to establish permission to access the ICP and Docker installation artifacts.
  - Default: `ibm-cloud-private`

- ICPBootNodeScriptPackagePath
  - The path in the S3 bucket to the ICP Boot node script package (zip) file. **DO NOT** include a leading / on the path value.
  - Default: `scripts/aws-icp-bootstrap.zip`

- ICPClusterNodeScriptPackagePath
  - The path in the S3 script bucket to the ICP cluster node script package (zip) file. **DO NOT** include a leading / on the path value. Cluster nodes are master, proxy, worker, management, vulnerability advisor.
  - Default: `scripts/aws-icp-nodeinit.zip`

- *[QS doc]* ICPDeploymentLogsBucketName (**required**)
  - The name of the S3 bucket where ICP stack deployment logs are to be exported. The deployment logs provide a record of the boot strap scripting actions and are useful for problem determination if the deployment fails in some way.

- *[QS doc]* ICPInstallationTimeout
  - The timeout (in seconds) associated with the installation and configuration of the ICP cluster, from start to finish. The `ICPInstallationTimeout` must be equal or greater than the `InceptionTimeout`. The `ICPInstallationTimeout` needs to be sufficient to allow the bootstrap installation script to complete.  See `InceptionTimeout` for some guidance on expected installation time.
  - Default: `7200`

- *[QS doc]* ICPVersion
  - The version of ICP to be deployed. The full version must be provided, e.g., 3.1.0.
  - Default: `3.1.0`

- InceptionTimeout
  - The number of seconds to wait for the IBM Cloud Private inception container to complete the installation.  For a small HA cluster (12 nodes) the inception process typically completes the installation in about 60 minutes. The start-to-finish installation time is on the order of 75 minutes for such a cluster.
  - Default: `7200`

- *[QS doc]* KeyFilePath
  - Path to a file in the ICP script bucket (`QSS3BuckeName`) with public keys for administrators who need SSH access to the boot node. The public keys in the file in S3 at the KeyFilePath are copied to the `authorized_keys` file of the `ubuntu` user on the boot node.  
  - Default: ''

- *[QS doc]* KeyName (**required**)
  - Name of an existing EC2 KeyPair to enable SSH access to the instance
  - Must be the name of an existing EC2 KeyPair defined in the region where the deployment is to occur.

- *[QS doc]* ManagementNodeCount:
  - Number of Management nodes to be deployed in the ICP cluster. For a dev deployment 1 is sufficient. For production deployments, at least 2 and typically 3 are deployed.  The management nodes run the resource and log monitoring components, e.g., Prometheus, Grafana and the ELK stack.
  - Default: 1

- *[QS doc]* ManagementNodeInstanceType
  - ICP management node AWS EC2 instance type
  - Default: `m5.2xlarge`

- *[QS doc]* MasterNodeCount
  -  Number of master nodes to be deployed in the ICP cluster. Must be an odd number. For a development deployment 1 is sufficient; for production deployment 3.  Currently, the master node count can only be 1 or 3.
  - Default: 1

- *[QS doc]* MasterNodeInstanceType
  - ICP master node AWS EC2 instance type.
  - Default: `m5.2xlarge`

- *[QS doc]* PrivateSubnetCIDR:
  - The CIDR block to be used for the private subnets. The `PrivateSubnetCIDR` must be within the network defined by the `VPCCIDR` and not overlap with the `PublicSubnetCIDR`
  - Default: 10.10.10.0/20

- *[QS doc]* PrivateSubnets:
  - A list of CIDR blocks to be used for the private subnets defined in 1 or 3 Availability Zones.  If there is only 1 Availability Zone, then the subnet can be the same as the `PrivateSubnetCIDR`.  The private subnets cannot overlap and must be within the `PrivateSubnetCIDR`. NOTE: CommaDelimitedList is invalid to pass into child templates.  Type is declared String, but it is intended to be a comma delimited list. Sample for 3 AZs: 10.10.10.0/24, 10.10.11.0/24, 10.10.12.0/24
  - Default: 10.10.10.0/24

- *[QS doc]* ProxyNodeCount
  - Number of Proxy nodes to be deployed in the ICP cluster. For a dev deployment 1 is sufficient. For production deployments, at least 2 and typically 3 are deployed.
  - Default: 1

- *[QS doc]* ProxyNodeInstanceType
  - ICP Proxy node AWS EC2 instance type
  - Default: `m5.xlarge`

- *[QS doc]* PublicSubnetCIDR
  - CIDR block used for the public subnets.  The `PublicSubnetCIDR` is used for defining public subnet security groups.  The `PublicSubnetCIDR` must be within the network defined by the `VPCCIDR` and not overlap with the `PrivateSubnetCIDR`.
  - Default: 10.10.20.0/22

- *[QS doc]* PublicSubnets
  - List of CIDRs to be used for 1 or 3 public subnets of the VPC. The number of CIDRs provided must equal the number of Availability Zones (`AvailabilityZoneCount`). The public subnets cannot overlap and must be within the network defined by the `PublicSubnetCIDR`.  NOTE: CommaDelimitedList is invalid to pass into child templates.  Type is declared String, but it is intended to be a comma delimited list.  Sample for 3 AZs: 10.10.20.0/24, 10.10.21.0/24, 10.10.22.0/24
  - Default: 10.10.20.0/24

- *[QS doc]* QSS3BucketName: (**required**)
  - The name of the S3 bucket where most of the ICP installation artifacts (scripts, templates, etc) are located. This bucket holds all of the content of the QuickStart git repository for IBM Cloud Private which includes the script packages for the boot node and the cluster nodes.  This bucket also holds the cloud formation templates that defines the ICP infrastructure deployed in the AWS cloud.

- *[QS doc]* QSS3KeyPrefix:
  - The "context root" of the content for the ICP QuickStart.  By convention it is required that the value of the `QSS3KeyPrefix` is the name of the git repository associated with the IBM Cloud Private QuickStart artifacts.
  - Default: `quickstart-ibm-cloud-private`

- *[QS doc]* ResourceOwner (**required**)
  - Value for the owner tag for the deployed resources associated with the stacks that get deployed.

- *[QS doc]* ServiceCIDR
  - The CIDR for the ICP service overlay network.  This gets assigned to the `service_cluster_ip_range` attribute in `config.yaml`.  The value provided must be a network that does not conflict with the AWS VPC network (`VPCCIDR`).  It also must not conflict with the ICP cluster overlay network (`ClusterCIDR`).
  - Default: `172.16.0.0/24`

- *[QS doc]* VPCCIDR
  - The VPC CIDR block. Must be in the form x.x.x.x/16-28.  This is the CIDR for the "underlay" network provided by AWS.
  - Default: `10.10.0.0/16`

- *[QS doc]* VPCDomain:
  - The network domain of the VPC.  The `VPCDomain` is used when defining the hosted zone. The `ClusterName` and the `VPCDomain` are combined to form the `ClusterDNSName` which is used in the ICP configuration for the `cluster_CA_domain` parameter in the `config.yaml` file.  (If PKI certificates are provided for the deployment the CN used for creating the certificates must match the value of `ClusterName` concatenated with a dot and the value of the `VPCDomain`.)
  - Default: `example.com`

- *[QS doc]* VPCName
  - The name of the deployed Virtual Private Cloud
  - Default: `IBMCloudPrivateVPC`

- VulnerabilityAdvisorNodeCount
  - Number of Vulnerability Advisor nodes to be deployed in the ICP cluster. Not typically deployed for a development environment. For production deployments, typically 3 are deployed.  VA uses zookeeper which requires an odd number of instances for consistency voting purposes. The VA nodes run the resource image and container security scanning components. (NOTE: Not currently supported.)
  - Default: 1

- VulnerabilityAdvisorNodeInstanceType:
  - ICP Vulnerability Advisor node AWS EC2 instance type
  - Default: `m5.2xlarge`

- WhichProxyLBAddress:
  - The value to use for the proxy load balancer address.  This value is used to drive the logic in the bootstrap script.
  - AllowedValues:
    - UseProxyELBAddress
    - UseProxyELBName
    - UsePrimaryAppDomain
  - Default: `UsePrimaryAppDomain`

- *[QS doc]* WorkerNodeCount
  - Number of worker nodes (desired capacity) to be deployed in the ICP cluster.
  - Default: 2

- *[QS doc]* WorkerNodeInstanceType
  - ICP Worker node AWS EC2 instance type
  - Default: `m5.xlarge`
