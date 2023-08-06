# FarSSH
Secure on-demand tunnel into AWS VPCs

# Installation

#### Deploy configuration on AWS

Use this [Cloudformation quick-create link](https://console.aws.amazon.com/cloudformation/home#/stacks/create/review?templateURL=https://farssh.s3.amazonaws.com/cloudformation/farssh.yaml&stackName=farssh-default) to deploy the following resources:
  * IAM roles for the ECS task (TaskRole and ExecutionRole)
  * ECS resources: cluster `farssh`, task definition `farssh-default`
  * SSM Parameters `/farssh/*`
  * Security Group `farssh-default`

#### Allow connections from FarSSH

Adjust your existing Security Groups to allow inbound connections from the FarSSH Security Group.

For example, to allow tunnel connections to your RDS instance, modify a corresponding RDS instance Security Group:
* Edit *inbound rules*
* Type: PostgreSQL (or MySQL or ...)
* Source: custom: security group `farssh-default`

#### Download the FarSSH client

Download the [client](https://raw.githubusercontent.com/apparentorder/farssh/main/client/farssh) (shell script),
place it appropriately, e.g. in your `~/bin/` directory, and make it executable.

For example:
```
curl -o ~/bin/farssh https://raw.githubusercontent.com/apparentorder/farssh/main/client/farssh
chmod 755 ~/bin/farssh
```

The client requires and uses the `aws` cli in your environment; the AWS target account, region and
credentials therefore depend on your environment (awscli config and/or environment variables).

Make sure that your local environment uses the same AWS account and region that you deployed the
Cloudformation template to.
