import os
import shutil

from farssh.const import *

def build_commands(args, ssh_keys, ip_address, database):
	ssh_command  = [ shutil.which("ssh") ]
	ssh_command += [ "-p", args.ssh_port ]
	ssh_command += [ "-o", f"IdentityFile {ssh_keys.login_key_file}" ]
	ssh_command += [ "-o", f"IdentitiesOnly yes" ]
	ssh_command += [ "-o", f"UserKnownHostsFile {ssh_keys.known_hosts_file}" ]
	ssh_command += [ "-o", f"StrictHostKeyChecking yes" ]
	ssh_command += [ "-o", f"ExitOnForwardFailure yes" ]
	ssh_command += [ "-l", f"root" ]

	main_command = None

	if args.cmd_args.get('command') == "ssh":
		ssh_command += [ ip_address ]
		ssh_command += args.cmd_args.get('extra_arguments')

		print("------------------------------------------------------------------------")
		print()

	elif args.cmd_args.get('command') == "proxy":
		ssh_command += [ "-D", "1080" ]
		ssh_command += [ ip_address ]
		ssh_command += [ "echo SOCKS proxy available on port 1080. Hit Ctrl-C to terminate.; sleep infinity" ]

	elif args.cmd_args.get('command') in [ "psql", "mysql" ]:
		port = str(database['port'])

		l_args = [ port, database['hostname'], port ]
		ssh_command += [ "-L", ":".join(l_args) ]
		ssh_command += [ ip_address ]

		if args.cmd_args.get('command') == "psql":
			username = args.cmd_args.get('username') or os.environ.get('PGUSER') or database.get('username')
			database = args.cmd_args.get('database') or os.environ.get('PGDATABASE') or database.get('database') or 'template1'
			main_command  = [ "psql" ]
			main_command += [ "--host", "localhost" ]
			main_command += [ "--port", port ]
			main_command += args.cmd_args.get('extra_arguments')
			main_command += [ database ]
			main_command += [ username ]
		elif args.cmd_args.get('command') == "mysql":
			username = args.cmd_args.get('username') or database.get('username')
			database = args.cmd_args.get('database') or database.get('database') or 'mysql'
			main_command  = [ "mysql" ]
			main_command += [ "--protocol", "tcp" ] # defaults to local socket otherwise
			main_command += [ "--host", "localhost" ]
			main_command += [ "--port", port ]
			main_command += [ "--user", username ]

			if args.cmd_args.get('password'):
				# we intentionally only support -p without an argument; it would
				# create ambiguity for argparse otherwise.
				main_command += [ "-p" ]

			main_command += args.cmd_args.get('extra_arguments')
			main_command += [ database ]

	elif args.cmd_args.get('command') == "tunnel":
		l_args = [
			args.cmd_args.get('local_port'),
			args.cmd_args.get('remote_host'),
			args.cmd_args.get('remote_port'),
		]

		ssh_command += [ "-L", ":".join(l_args) ]
		ssh_command += [ ip_address ]
		ssh_command += [ "echo Port forwarding tunnel established. Hit Ctrl-C to terminate.; sleep infinity" ]

	if main_command:
		mc_path = shutil.which(main_command[0])

		if not mc_path:
			raise SystemExit(f"ERROR:  Command {main_command[0]} not found")

		main_command[0] = mc_path

	return (ssh_command, main_command)

