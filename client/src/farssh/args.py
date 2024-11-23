#!/usr/bin/env python3

import argparse
import sys

from farssh.const import *
from farssh.aws import get_farssh_ssm_parameters

class FarsshArguments:
	def __init__(self):
		self.cmd_args = self._parse_args()
		self.cmd_args['remote_port'] = self.cmd_args.get('remote_port') or self.cmd_args.get('local_port')

		self.enable_execute_command = False

		# defaults, if not found in Parameter Store
		self.force_public_ipv4 = False

		for (key, value) in get_farssh_ssm_parameters(FARSSH_ID).items():
			setattr(self, key, value)

		try:
			self.public_subnets = self.public_subnets.split(',')
			self.force_public_ipv4 = (self.force_public_ipv4 == "true")
		except AttributeError:
			x  = f"ERROR:  FarSSH parameters not found for this AWS account and region. "
			x += f"Please follow setup instructions at {FARSSH_URL} first."
			raise SystemExit(x)

		# assign_public_ipv4 is not set from Parameter Store, but set here dynamically. It has to be sent from
		# the client (network configuration in ecs:RunTask), but the AWS side can set force_public_ipv4 to
		# signal the client that the server side needs public IPv4, e.g. for pulling the FarSSH image without NAT.
		# Otherwise, and if we're going to use IPv6 anyway, we don't need public IPv4.
		self.assign_public_ipv4 = "ENABLED" if self.force_public_ipv4 or not self.cmd_args.get('ipv6') else "DISABLED"

	def _parse_args(self):
		# TODO: the old syntax from v0.1, where it's possible to omit the "tunnel" command word,
		# seems to be impossible with python's argparse. figure out a way to support this again.

		if len(sys.argv) == 1:
			sys.argv += [ "--help" ]

		parser = argparse.ArgumentParser(
			description = "Secure on-demand connections into AWS VPCs",
		)

		parser.add_argument('-6', '--ipv6', action='store_true', help = 'use IPv6 (disables public IPv4 when possible)')
		parser.add_argument('-V', '--version', action='version', version = f'FarSSH {FARSSH_VERSION}')

		subparsers = parser.add_subparsers(dest = 'command', required = True)

		parser_ssh = subparsers.add_parser('ssh', help = 'start interactive SSH session')
		parser_ssh.add_argument('extra_arguments', nargs = '*', help = 'extra arguments passed to ssh')

		parser_proxy = subparsers.add_parser('proxy', help = 'start SOCKS proxy')

		parser_tunnel = subparsers.add_parser('tunnel', help = 'establish a port-forwarding tunnel')
		parser_tunnel.add_argument('local_port', help='local port number')
		parser_tunnel.add_argument('remote_host', help='remote host address')
		parser_tunnel.add_argument('remote_port', help='remote port (optional)', nargs = '?', default = argparse.SUPPRESS)

		parser_psql = subparsers.add_parser('psql', help = 'establish tunnel to a postgres endpoint and launch the psql client')
		parser_psql.add_argument('-i', '--identifier', help='database identifier (RDS)')
		parser_psql.add_argument('-u', '--user', dest='username', help='database username')
		parser_psql.add_argument('-U', '--username', help=argparse.SUPPRESS)
		parser_psql.add_argument('database', nargs = '?', help='database name (in the DB engine)')
		parser_psql.add_argument('extra_arguments', nargs = '*', help = 'extra arguments passed to psql')

		parser_mysql = subparsers.add_parser('mysql', help = 'establish tunnel to a mysql/mariadb endpoint and launch the mysql client')
		parser_mysql.add_argument('-i', '--identifier', help='database identifier (RDS)')
		parser_mysql.add_argument('-p', '--password', dest='password', action='store_true', help='ask for mysql password (pass -p to the mysql client)')
		parser_mysql.add_argument('-u', '--user', dest='username', help=argparse.SUPPRESS)
		parser_mysql.add_argument('-U', '--username', help='database username')
		parser_mysql.add_argument('database', nargs = '?', help='database name (in the DB engine)')
		parser_mysql.add_argument('extra_arguments', nargs = '*', help = 'extra arguments passed to mysql')

		return vars(parser.parse_args())

