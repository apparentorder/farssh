#!/usr/bin/env python3

import subprocess

from farssh.const import *
from farssh.args import FarsshArguments
from farssh.ssh import FarsshSshKeyHandler
from farssh.commands import build_commands
import farssh.aws as aws

def main():
	args = FarsshArguments()
	ssh_keys = FarsshSshKeyHandler(args)
	database = aws.select_database(args) if args.cmd_args.get('command') in ["psql", "mysql"] else None
	target_ip_address = aws.run_ecs_task(args, ssh_keys, FARSSH_ID)

	ssh_keys.write_known_hosts(target_ip_address)
	(ssh_command, main_command) = build_commands(args, ssh_keys, target_ip_address, database)

	if not main_command:
		try:
			subprocess.run(ssh_command)
		except KeyboardInterrupt:
			pass

		exit(0)

	ssh_command.insert(1, "-n") # StdinNull
	ssh_command += [ "echo connected; sleep infinity" ]

	with subprocess.Popen(ssh_command, stdout = subprocess.PIPE, stdin = subprocess.DEVNULL, text = True) as ssh:
		try:
			ssh_out = ssh.stdout.readline().strip() # wait for "connected"
			ssh.stdout.close()

			print(f"Tunnel connection established.")
			print(f"Running {' '.join(main_command)}")
			print("------------------------------------------------------------------------")

			subprocess.run(main_command)

		finally:
			ssh.terminate()

if __name__ == "__main__":
	main()

