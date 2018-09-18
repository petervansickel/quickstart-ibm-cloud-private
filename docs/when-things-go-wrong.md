# When things go wrong

This section captures common deployment problems and the solution.

## Cannot SSH to the boot node or any of the cluster nodes

The deployment has gotten to the point where the various stack templates have reached a state of `CREATE_COMPLETE`, yet when you attempt `ssh` to the public DNS name of the boot node, or any of the cluster nodes, the connection does not occur and eventually the attempt times out.

**Solution:**

Make sure your laptop IP address is within the inbound CIDR defined for `ExternalSSHSecurityGroup`.

Depending on your network provider, your IP address may change even though you did not disconnect from the network.

The `ExternalSSHSecurityGroup` inbound rules can be edited to allow your laptop to get in.

## After deployment, connection timeout to the ICP management console

When you attempt to access the ICP management console, there is a long wait that ends with a connection timeout.

**Solution:**

*TODO:* Need to investigate further.  The `ClusterCADomain` value may be what matters.  It just so happens that `ClusterCADomain` defaults to `ClusterName.ClusterDomain`.  The `ClusterCADomain` value is used to create the TLS PKI artifacts.  And that defaults to `mycluster.icp`.  But if the deployer sets a specific value for `ClusterCADomain` a misconfiguration could occur. The CN value of the generated TLS certificates for the cluster will not be the same as the value entered in Route53 that gets an alias to the master node ELB public DNS name.

You need to put an entry your laptop `/etc/hosts` file that maps the master node ELB public DNS name to `clustername.clusterdomain`, for example:
```
54.241.72.233      mycluster.icp
```

You also need to be sure the `ExternalICPAdminSecurityGroup` has an inbound rule that permits the IP address of your laptop to access the cluster on port 8443 (and port 8080 if you want to use that port).  

*NOTE:* This is not likely relevant.  There is now a security group named `ICPMasterSecurityGroup` and it permits all IP addresses.  If the value of `ExternalICPAdminLocation` in the parameters that were provided to the deployment is not a CIDR that includes your laptop's IP address, then you won't have access and the connection attempt to the ICP management console will time out.

The `ExternalICPAdminSecurityGroup` inbound rules can be edited to allow your laptop to get in.

A Route53 hosted zone must include the value of `clustername.clusterdomain` (or `ClusterCADomain` (TBD)) mapped to the public DNS name of the master node ELB. To confirm, open the admin page for the AWS Route53 service and clicked on the hosted zones.

*NOTE:* Try a different browser.  FireFox Quantum version 60.2 gets stuck in a TLS handshake when interacting with the ICP management console.  Chrome works just fine with the usual warning about the PKI certificate.



## After deployment, management console OAuth error: redirect URI not valid

You see an error that looks like:
```
CWOAU0062E: The OAuth service provider could not redirect the request because the redirect URI was not valid. Contact your system administrator to resolve the problem.
```

**Solution:**

Make sure the value used for `cluster_CA_domain` is the value of the host name you are using in the URL to get to the management console.

The value in the `cluster_CA_domain` needs to resolve to the master node ELB public IP address. One of the `Outputs` of the root template is the public DNS name of the master node ELB.  Do an `nslookup` on that ELB DNS name to get the public IP address of the master node ELB.  You can map that IP address to the `cluster_CA_domain` hostname in your laptop's `/etc/hosts` file.  If you are setting up a production deployment then work with your network administrator to create an entry in your organization's DNS that maps the `cluster_CA_domain` host to the master node ELB IP address.

Once you get things configured correctly, you may need to clear your browser cookies (clear history) to get the request to flow through to the management console login page.

## After deployment, a 500 server error is reported by the management console

You may see this problem when testing multiple ICP deployments.

**Solution:**

Clear browser history, specifically cookies from interaction with an earlier deployment.
