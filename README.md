# FarSSH

FarSSH provides secure on-demand tunnels into AWS VPCs.

This way you can easily connect to in-VPC resources like RDS and OpenSearch using tools installed on your local machine.

FarSSH also features a SOCKS proxy mode, enabling your browser to be "in" the target VPC; this works both for accessing VPC
resources and, optionally, as a quick way to tunnel all your browser traffic, so your browser's connections will
appear to come from this VPC's IP addresses.

FarSSH sessions will incur AWS charges only when you use it, at roughly $0.01 per hour, calculated per second
(Fargate billing model).

# Usage

#### Tunnel mode

Forward a local port to your VPC like this:
```
farssh tunnel 5432 pg-cluster.cluster-foo.eu-central-1.rds.amazonaws.com
```

Then connect to the local port 5432 on your machine, e.g. just using `psql -h localhost`.

#### Proxy mode

Simply run
```
farssh proxy
```

Then configure your browser to use a SOCKS proxy on `localhost`, port 1080.

#### SSH mode

If you need a shell inside your VPC, run
```
farssh ssh
```

# Installation

#### Deploy configuration on AWS

Use this [Cloudformation quick-create link](https://console.aws.amazon.com/cloudformation/home#/stacks/create/review?templateURL=https://farssh.s3.amazonaws.com/cloudformation/farssh.yaml&stackName=farssh-default) to deploy necessary
resources in the target environment. Make sure you have selected the correct region! For a list of created resources,
see below.

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
curl -o ~/bin/farssh \
https://raw.githubusercontent.com/apparentorder/farssh/main/client/farssh

chmod 755 ~/bin/farssh
```

The client requires and uses the `aws` cli in your environment; the AWS target account, region and
credentials therefore depend on your environment (awscli config and/or environment variables).

**Note:** Make sure that your local environment uses the same AWS account and region that you deployed the
Cloudformation template to.

# How it works

FarSSH consists of three rather simple components:

#### Container image

FarSSH publishes a container image in AWS Public ECR at `public.ecr.aws/apparentorder/farssh`. This is
a tiny Alpine-based image that only runs an SSH server. There is also a background process that will
terminate the task if there are no active connections.

#### Resources in the target environment

The Cloudformation template creates the following resources so FarSSH tasks can be run in the target
environment:

  * IAM roles for the ECS task (TaskRole and ExecutionRole)
  * ECS resources: cluster `farssh`, task definition `farssh-default`
  * SSM Parameters `/farssh/*`
  * Security Group `farssh-default`

#### Client

The "client" is a relatively simple shell script that pulls a few parameters from SSM Parameter Store
and then starts an ECS Task with the FarSSH image. The FarSSH task will be available after a few seconds.
The client will then start an `ssh` session as appropriate for the desired connection mode. Key pairs are
generated locally for both the client connection and the FarSSH task's SSH host key, and the SSH client
will "strictly" check the expected host key.
