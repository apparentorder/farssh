#!/usr/bin/env python3

import subprocess
import tempfile

# ----------------------------------------------------------------------

class FarsshSshKeyHandler:
	def __init__(self, farssh_args):
		self._tempdir = tempfile.TemporaryDirectory()

		self.farssh_args = farssh_args
		self.known_hosts_file = f"{self._tempdir.name}/known-hosts"

		subprocess.run(["ssh-keygen", "-q", "-N", "", "-t", "rsa", "-f", f"{self._tempdir.name}/ssh_host_rsa_key"], check = True)
		subprocess.run(["ssh-keygen", "-q", "-N", "", "-t", "rsa", "-f", f"{self._tempdir.name}/ssh_login_key"], check = True)

		self.host_key_file =      f"{self._tempdir.name}/ssh_host_rsa_key"
		self.host_key_pub_file =  f"{self._tempdir.name}/ssh_host_rsa_key.pub"
		self.login_key_file =     f"{self._tempdir.name}/ssh_login_key"
		self.login_key_pub_file = f"{self._tempdir.name}/ssh_login_key.pub"

		self.host_key = open(self.host_key_file, "r").read()
		self.host_key_pub = open(self.host_key_pub_file, "r").read()
		# self.login_key = open(self.login_key_file, "r").read() # not used
		self.login_key_pub = open(self.login_key_pub_file, "r").read()

	def write_known_hosts(self, ip_address):
		# Create temporary known-hosts file so the SSH client can verify the remote host's public key that we configured it with.
		# The `host` *must* be without port number when the port is 22; this seems to be a quirk of OpenSSH's known-hosts file format.

		with open(self.known_hosts_file, "w") as f:
			host = ip_address

			if self.farssh_args.ssh_port != "22":
				host = f"[{host}]:{self.farssh_args.ssh_port}"

			f.write(f"{host} {self.host_key_pub}\n")

