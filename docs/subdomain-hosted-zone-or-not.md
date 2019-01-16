# Logic for sub-domains and hosted zones

## Notes

When the AWS::Route53::HostedZone is created, if the `VPCs` property is specified, then the hosted zone is private.

A cluster specific AWS::Route53::HostedZone does not get created if the HostedZoneId parameter has a non-empty value.  (The VPCHostedZone already exists.)


## Controlling behavior

The influencing parameters:
- HostedZoneId - default value ''
- VPCDomain - default value ''
- VPCSubdomainPrefix - default value ''

To create a hosted zone specific to the ICP deployment (VPCHostedZone), leave the HostedZoneId with an empty string value.

To use an existing hosted zone pass in the hosted zone ID in the HostedZoneId parameter.

To create a subdomain hosted zone, provide a HostedZoneId and a VPCSubdomainPrefix.

If a HostedZoneId is not provided, and a VPCSubdomainPrefix is provided, the VPCSubdomainPrefix is prepended to the VPCDomain and the VPCHostedZone domain is composed by joining the values in VPCSubdomainPrefix and VPCDomain separated by a dot.
