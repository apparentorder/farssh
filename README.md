## FarSSH

FarSSH provides secure on-demand connections into AWS VPCs.

You can easily connect to in-VPC resources like RDS and OpenSearch endpoints, using tools installed on your local machine.

FarSSH features a SOCKS proxy mode, enabling your browser to be "in" the target VPC; this works both for accessing VPC
resources and as a quick way to tunnel all your browser traffic, so your browser's connections will
appear to come from this AWS region's public IP addresses (like a VPN).

FarSSH integrates with the `psql` and `mysql` command line clients for easy database access.

Resources are deployed in *your* AWS account; there is no third party / no external service involved. AWS charges apply,
at roughly $0.01 per hour (billed per second) per active client; no charges when no client is active.


## Usage

### SQL Client Mode

To launch a `psql` or `mysql` client directly to one of your RDS databases (instance or cluster), simply:
```
farssh psql [-U username] [database_name]
```

For MySQL / MariaDB:
```
farssh mysql -p [-u username] [database_name]
```

When not specified, username and database_name will be taken from the RDS configuration (master username and the
initial database).

If only one matching RDS database is available, it will automatically be selected. If there are multiple databases,
use `--identifier` to select one; otherwise, a list of available databases will be shown.

### Tunnel mode

Forward a local port to your VPC like this:
```
farssh tunnel 5432 pg-cluster.cluster-foo.eu-central-1.rds.amazonaws.com
```

Then connect to the local port 5432 on your machine, e.g. just using `psql -h localhost` in another shell, or your favorite GUI client.

Remember to terminate the FarSSH session using `^C` when done.

### Proxy mode

Simply run
```
farssh proxy
```

Then configure your browser to use a SOCKS proxy on `localhost`, port 1080.

Remember to terminate the FarSSH session using `^C` when done.

### SSH mode

If you just need a shell inside your VPC, run
```
farssh ssh
```

### Additional Arguments

The `psql`, `mysql` and `ssh` commands can be used with additional arguments that will be passed to the client, so you
could do something like `farssh ssh -- /sbin/ip address` or `farssh psql -- -c "select foo from bar"`.


## Installation

### Requirements

 * The target VPC needs to have a public subnet
   * note that the connection target (FarSSH tunnel mode) can be in a private subnet, or, via VPC peering, even
     in a different VPC
 * For the client machine:
   * local AWS configuration (appropriate credentials / profiles configured etc.)
   * Python 3
   * [AWS SDK for Python](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html), aka `boto3`
   * OpenSSH `ssh` client
   * The `psql` / `mysql` command line utilities if you want to use the respective mode

### Deploy configuration on AWS

Use this [Cloudformation quick-create link](https://console.aws.amazon.com/cloudformation/home#/stacks/create/review?templateURL=https://farssh.s3.amazonaws.com/cloudformation/farssh.yaml&stackName=farssh-default) to deploy necessary
resources in the target environment.

For Subnets, be sure to select one or more *public* subnets, i.e. that are connected to an Internet Gateway.

Make sure you have selected the correct region! For a list of created resources,
see below.

**NOTE: If you intend to use IPv6, please read below, before continuing**

**NOTE: If Cloudformation fails to create the stack with this error ...**
```
Unable to assume the service linked role. Please verify that the ECS service linked role exists.
```
... then please delete the stack from Cloudformation and simply retry from the quick-create link above.
That role is automatically created by AWS on first-ever ECS usage, but the cluster creation fails anyway. If
you know how to properly fix this in Cloudformation, please let me know.


### Allow connections from FarSSH

Adjust your existing Security Groups to allow inbound connections from the FarSSH Security Group.

For example, to allow tunnel connections to your RDS instance, modify a corresponding RDS instance Security Group:
* Edit *inbound rules*
* Type: PostgreSQL (or MySQL or ...)
* Source: custom: security group `farssh-default`

### Install the FarSSH client

The FarSSH client is available in the Python Package Index, so you can simply use `pip` to install and update:

```
pip install farssh
```

FarSSH will use the target AWS account, region and credentials from the local AWS configuration, e.g. your configuration in `~/.aws`,
your `AWS_PROFILE` and `AWS_REGION` environment variables etc.

**Note:** Make sure that your local environment uses the same AWS account and region that you deployed the
Cloudformation template to.

That's it. For usage, see above.


### Updating

To update the FarSSH client, simply re-download the client (see above).

To update the FarSSH Cloudformation template, select the FarSSH stack in the Cloudformation console, hit
"Update" and replace the template using this S3 url: `https://farssh.s3.amazonaws.com/cloudformation/farssh.yaml`

To update FarSSH settings, update the stack with the "Use current template" option.


## IPv6 Support

Given that AWS now charges for any use of public IPv4 addresses, it's important to use IPv6 when possible.

FarSSH supports IPv6 both on the AWS side and on the client.

### Client Side

Run the client with the option `-6` (or `--ipv6`) to make it connect to the FarSSH ECS task via IPv6. The
client will fail when the FarSSH ECS task does not have an IPv6 address.

### Server Side (ECS)

IPv6 for the FarSSH ECS task is a bit more complicated, as we need to work around several IPv6 potholes in AWS.

To allow IPv6 connections from the client, you only need to make sure that the configured public subnets have IPv6 configured.
Fargate tasks will automatically get an IPv6 address. If that doesn't work out of the box, double-check the ECS [`dualStackIPv6` setting](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs-account-settings.html).

But an ECS task also needs some IP connectivity to pull the image and to send logs to Cloudwatch. If you have neither VPC endpoints
nor NAT in your VPC, this will cause the ECS task to fail when a FarSSH client uses IPv6.

The Cloudformation template has some knobs for this:

The easy fix is to set `ForcePublicIpv4` to `true` in the Cloudformation stack; FarSSH will then always
request a public IPv4 address, even when a clients connects via IPv6. With the public IPv4 address, everything works.

Alternatively, to fully avoid using public IPv4 addresses, change these options during the Cloudformation setup:

- set `ImageUri` to the `docker.io` address (the AWS ECR does not support IPv6)
- disable the `awslogs` driver (Cloudwatch Logs does not support IPv6)


## How it works

FarSSH is basically a wrapper around an OpenSSH server and your local OpenSSH client. The latter does the
actual work of tunneling (local port forwarding, parameter `-L`) and proxying (SOCKS proxy, parameter `-D`).

FarSSH consists of three rather simple components to glue it together. Here's a highly professional
architecture diagram:

![farssh architecture painting](https://pbs.twimg.com/media/Fz776zoWIAI6f89?format=png&name=900x900)

### Container image

FarSSH publishes a container image in AWS Public ECR at `public.ecr.aws/apparentorder/farssh`. This is
a tiny Alpine-based image that only runs an SSH server. There is also a background process that will
terminate the task if there are no active connections.

The same image is also published to Dockerhub at `docker.io/apparentorder/farssh`, because Dockerhub
supports IPv6 and AWS Public ECR does not. Using Dockerhub over IPv4 might result in pull errors due
to rate limit though.

### Resources in the target environment

The Cloudformation template creates the following resources so FarSSH tasks can be run in the target
environment:

  * IAM roles for the ECS task (TaskRole and ExecutionRole)
  * ECS resources: cluster `farssh`, task definition `farssh-default`
  * SSM Parameters `/farssh/*`
  * Security Group `farssh-default`

### Client

The "client" pulls a few parameters from SSM Parameter Store
and then starts an ECS Task with the FarSSH image. The FarSSH task will be available after a few seconds.

The client will then start an `ssh` session to the public IP address of the FarSSH task.

Key pairs are generated locally for both the client connection and the FarSSH task's SSH host key, and
the SSH client will "strictly" check the expected host key.

### Caveats

* Currently, FarSSH can be deployed to only one VPC per region per account (deploying multiple times to
  different regions works fine)


## Future ideas

* Support for multiple VPCs per region
* Optionally use some kind of "reverse SSH", so the FarSSH task does not need a public IP address
* Enable using existing ECS clusters (possibly including EC2-based)
* Only half-way through building this I realized that I could have built the same thing for an
  ad-hoc VPN endpoint instead of an SSH server; I have yet to think through what kind of sense
  that could make
* Properly tag the public ECR image(s) so it can be coupled with released versions

 
  
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

I'm (still) trying to get used to X/Twitter as [@apparentorder](https://twitter.com/apparentorder). DMs are open.
You can also try legacy message delivery to apparentorder@neveragain.de.

