# Limitations

This section describes the limitations of the current release.

- *[QS doc]* ICP 3.1.0 is the currently supported version of ICP.  

- *[QS doc]* The latest version of FireFox Quantum (v60.2.0esr) times out doing the TLS handshake. The issue is likely due to the self-signed cert that gets generated as part of the ICP configuration. Earlier versions of FireFox were working. Chrome does work.  Other browsers have not been tested.  

- *[QS doc]* Using ICP Community Edition is not currently supported.

- *[QS doc]* The EC2 instances are all based on Ubuntu.  The UserData code is specific to Ubuntu package manager.  There may be other ubuntu specific implementation details. The AMI images are all Ubuntu 16.04.

- *[QS doc]* Vulnerability Advisor is not currently supported.

- *[QS doc]* Deploying an ICP cluster with dedicated `etcd` nodes is not currently supported.
 
- *[QS doc]* Automatically scaling up and down the number of worker nodes after cluster deployment is not currently supported.

- Different EC2 instance types for worker nodes is not currently supported.  At least with a single auto-scaling group for worker nodes, different EC2 instance types is not possible. We could have multiple worker node auto-scaling groups, e.g., auto-scaling groups for T-shirt sizes.  Need to investigate. What happens if the node count for an auto-scaling group is 0?  
