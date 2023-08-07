## FarSSH

FarSSH provides secure on-demand tunnels into AWS VPCs.

This way you can easily connect to in-VPC resources like RDS and OpenSearch using tools installed on your local machine.
You could also access AWS resources that can only be access via specific VPC interface endpoints.

FarSSH features a SOCKS proxy mode, enabling your browser to be "in" the target VPC; this works both for accessing VPC
resources and, optionally, as a quick way to tunnel all your browser traffic, so your browser's connections will
appear to come from this VPC's IP addresses.

FarSSH sessions will incur AWS charges only when you use it, at roughly $0.01 per hour, calculated per second
(Fargate billing model).



## Usage

### Tunnel mode

Forward a local port to your VPC like this:
```
farssh tunnel 5432 pg-cluster.cluster-foo.eu-central-1.rds.amazonaws.com
```

Then connect to the local port 5432 on your machine, e.g. just using `psql -h localhost`.

### Proxy mode

Simply run
```
farssh proxy
```

Then configure your browser to use a SOCKS proxy on `localhost`, port 1080.

### SSH mode

If you need a shell inside your VPC, run
```
farssh ssh
```



## Installation

### Requirements

 * The target VPC needs to have a public subnet
   * note that the connection target (FarSSH tunnel mode) can be in a private subnet, or, via VPC peering, even
     in a different VPC
 * `aws` cli and appropriate credentials configured on the client machine

### Deploy configuration on AWS

Use this [Cloudformation quick-create link](https://console.aws.amazon.com/cloudformation/home#/stacks/create/review?templateURL=https://farssh.s3.amazonaws.com/cloudformation/farssh.yaml&stackName=farssh-default) to deploy necessary
resources in the target environment. Make sure you have selected the correct region! For a list of created resources,
see below.

### Allow connections from FarSSH

Adjust your existing Security Groups to allow inbound connections from the FarSSH Security Group.

For example, to allow tunnel connections to your RDS instance, modify a corresponding RDS instance Security Group:
* Edit *inbound rules*
* Type: PostgreSQL (or MySQL or ...)
* Source: custom: security group `farssh-default`

### Download the FarSSH client

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



## How it works

FarSSH is basically a wrapper around an OpenSSH server and your local OpenSSH client. The latter does the
actual work of tunneling (local port forwarding, parameter `-L`) and proxying (SOCKS proxy, parameter `-D`).

FarSSH consists of three rather simple components to glue it together:

### Container image

FarSSH publishes a container image in AWS Public ECR at `public.ecr.aws/apparentorder/farssh`. This is
a tiny Alpine-based image that only runs an SSH server. There is also a background process that will
terminate the task if there are no active connections.

### Resources in the target environment

The Cloudformation template creates the following resources so FarSSH tasks can be run in the target
environment:

  * IAM roles for the ECS task (TaskRole and ExecutionRole)
  * ECS resources: cluster `farssh`, task definition `farssh-default`
  * SSM Parameters `/farssh/*`
  * Security Group `farssh-default`

### Client

The "client" is a relatively simple shell script that pulls a few parameters from SSM Parameter Store
and then starts an ECS Task with the FarSSH image. The FarSSH task will be available after a few seconds.

The client will then start an `ssh` session as appropriate for the desired connection mode.

Key pairs are generated locally for both the client connection and the FarSSH task's SSH host key, and
the SSH client will "strictly" check the expected host key.

### Caveats

* Currently, FarSSH can be deployed to only one VPC per region per account (deploying multiple times to
  different regions works fine)
* This is a brand-new project, so please do use and test it, but keep this in mind before using
  it in production environments


## Future ideas

* Re-write the client in an actual programming language, because right now it's slow and ugly
* Support for multiple VPCs per region
* Support for IPv6(-only)
* Optionally use some kind of "reverse SSH", so the FarSSH task does not need a public IP address
* Enable using existing ECS clusters (possibly including EC2-based)
* Only half-way through building this I realized that I could have built the same thing for an
  ad-hoc VPN endpoint instead of an SSH server; I have yet to think through what kind of sense
  that could make

 
  
## Motivation

To my knowledge, all alternative options use [time-based billing](https://tty.neveragain.de/2021/06/29/timeless-services.html),
meaning that you pay a base fee for having them around, even if you're not using them at all.
For example, while AWS ClientVPN does charge per connection hour, it also charges you just for
being associated to your VPC.

AWS recently announced [EC2 Instance Connect Endpoints](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/connect-using-eice.html)
which absolutely solve this problem, even without additional charges. For a few days after release, this
allowed to make arbitrary TCP connections (e.g. to your RDS instance's port 5432!).

Unfortunately, AWS decided that while this works great and allows most customer to get rid of jump hosts
once and for all, it's just too easy. As it stands today, it's artificially limited to target ports 22 (ssh)
and 3389 (RDP). This move also influenced this project's name: While "FarSSH" is a play on "Fargate" and "SSH",
it shall be pronounced "farce" – because this project shouldn't have to exist.



## Contact

For bug reports, pull requests and other issues please use Github.

For everything else:

I'm (still) trying to get used to Twitter as @apparentorder. DMs are open.
You can also try legacy message delivery to apparentorder@neveragain.de.
