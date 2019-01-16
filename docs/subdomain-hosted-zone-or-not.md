# Logic for sub-domains and hosted zones

## Notes

When the AWS::Route53::HostedZone is created, if the `VPCs` property is specified, then the hosted zone is private.

A cluster specific AWS::Route53::HostedZone does not get created if the VPCHostedZone parameter has a non-empty value.  (The VPCHostedZone already exists.)


## Controlling behavior

The influencing parameters:
- VPCDomain - default value ''
- VPCHostedZoneId - default value ''
- VPCSubdomainPrefix - default value ''

To create a hosted zone specific to the ICP deployment leave the VPCHostedZoneId with an empty string value.

To use an existing hosted zone pass in the hosted zone ID in the VPCHostedZoneId parameter.
