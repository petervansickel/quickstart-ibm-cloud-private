# Limitations

This section describes the limitations of the current release.

- ICP 2.1.0.3 and ICP 3.1.0.0 have been tested.  

- ICP 2.1.0.3 Fixpack 1 has been installed but not tested much.  Installing the fixpack takes an additional 30 minutes or so.  It is recommended that the latest ICP supported by the QuickStart be used.

- The latest version of FireFox Quantum (v60.2.0esr) times out doing the TLS handshake. The issue is likely due to the self-signed cert that gets generated as part of the ICP configuration. Earlier versions of FF were working.   Chrome does work.  Other browsers have not been tested.  

- Using ICP Community Edition is not currently supported.  Modifying the installation scripts to support ICP Community Edition installs, should be relatively straight-forward.  Using ICP CE has not been a focus of MVP1.

- The EC2 instances are all based on Ubuntu.  The UserData code is specific to Ubuntu package manager.  There may be other ubuntu specific implementation details.

- Bring your own PKI certificates is not currently supported. This would be relatively easy to support.  Need to add parameters to point to S3 bucket to get the certificates and copy them into the appropriate directory as part of the inception configuration script.

- All of the cluster node types are deployed using AWS auto-scaling groups to allow the number of each type of node to be configure at deployment time.  However, scaling up and down after cluster deployment is not currently supported.  Scripts will need to be developed that get triggered when an auto-scaling event occurs so that the appropriate actions can be taken to add or remove a node to/from the cluster.  Presumably AWS CloudFormation has a framework for triggering such scripts upon auto-scaling events.  No research into the details has been done.

- Different EC2 instance types for worker nodes is not currently supported.  At least with a single auto-scaling group for worker nodes, different EC2 instance types is not possible. We could have multiple worker node auto-scaling groups, e.g., auto-scaling groups for T-shirt sizes.  Need to investigate. What happens if the node count for an auto-scaling group is 0?  

- *TBD*
