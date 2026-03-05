#!/usr/bin/env python3

import subprocess
import tempfile

# ----------------------------------------------------------------------

class FarsshSshKeyHandler:
	def __init__(self, farssh_args) -> None:
		self._tempdir = tempfile.TemporaryDirectory()

		self.farssh_args = farssh_args
		self.known_hosts_file = f"{self._tempdir.name}/known-hosts"

		subprocess.run(["ssh-keygen", "-q", "-N", "", "-t", "ed25519", "-f", f"{self._tempdir.name}/ssh_host_ed25519_key"], check = True)
		subprocess.run(["ssh-keygen", "-q", "-N", "", "-t", "rsa",     "-f", f"{self._tempdir.name}/ssh_host_rsa_key"], check = True)
		subprocess.run(["ssh-keygen", "-q", "-N", "", "-t", "ed25519", "-f", f"{self._tempdir.name}/ssh_login_key"], check = True)

		self.ed25519_host_key_file =      f"{self._tempdir.name}/ssh_host_ed25519_key"
		self.ed25519_host_key_pub_file =  f"{self._tempdir.name}/ssh_host_ed25519_key.pub"
		self.rsa_host_key_file =          f"{self._tempdir.name}/ssh_host_rsa_key"
		self.rsa_host_key_pub_file =      f"{self._tempdir.name}/ssh_host_rsa_key.pub"
		self.login_key_file =             f"{self._tempdir.name}/ssh_login_key"
		self.login_key_pub_file =         f"{self._tempdir.name}/ssh_login_key.pub"

		self.ed25519_host_key =           open(self.ed25519_host_key_file, "r").read()
		self.ed25519_host_key_pub =       open(self.ed25519_host_key_pub_file, "r").read()
		self.rsa_host_key =               open(self.rsa_host_key_file, "r").read()
		self.rsa_host_key_pub =           open(self.rsa_host_key_pub_file, "r").read()
		self.login_key_pub =              open(self.login_key_pub_file, "r").read()
		# self.login_key isn't used here, so don't read.

	def write_known_hosts(self, ip_address) -> None:
		# Create temporary known-hosts file so the SSH client can verify the remote host's public key that we configured it with.
		# The `host` *must* be without port number when the port is 22; this seems to be a quirk of OpenSSH's known-hosts file format.
		# Write Ed25519 key first (preferred), then RSA (fallback for backward compatibility).

		with open(self.known_hosts_file, "w") as f:
			host = ip_address

			if self.farssh_args.ssh_port != "22":
				host = f"[{host}]:{self.farssh_args.ssh_port}"

			f.write(f"{host} {self.ed25519_host_key_pub}\n")
			f.write(f"{host} {self.rsa_host_key_pub}\n")
