import base64
import boto3
import time

# ----------------------------------------------------------------------

def get_farssh_ssm_parameters(farssh_id):
	r = {}

	ssm = boto3.client('ssm')
	for param in ssm.get_parameters_by_path(Path = f"/farssh/{farssh_id}", Recursive = True)['Parameters']:
		param_name = param['Name'].split('/')[-1]
		r[param_name] = param['Value']

	return r

def select_ip_address(args, task):
	ipv4_address = None
	ipv6_address = task['containers'][0]['networkInterfaces'][0].get('ipv6Address')

	if args.cmd_args.get('ipv6'):
		if not ipv6_address:
			raise SystemExit("ERROR:  IPv6 requested, but no IPv6 address on the FarSSH ECS task. Check selected VPC subnets.")

		return ipv6_address

	# The IPv6 is available in `task`, but the public IPv4 address is not, so we need to query this separately.
	ec2 = boto3.client('ec2')
	eni_id = [detail['value'] for detail in task['attachments'][0]['details'] if detail['name'] == "networkInterfaceId"][0]
	dni = ec2.describe_network_interfaces(NetworkInterfaceIds = [ eni_id ])
	ipv4_address = dni['NetworkInterfaces'][0].get('Association', {}).get('PublicIp')

	if ipv4_address:
		return ipv4_address

	if ipv6_address:
		print("WARNING:  FarSSH ECS task has no public IPv4 address; attempting with IPv6.")
		return ipv6_address

	raise SystemExit("ERROR:  FarSSH ECS task has neither IPv6 nor public IPv4 address. Check selected VPC subnets.")

def run_ecs_task(args, ssh_keys, farssh_id):
	override_env = [
		{
			"name": "FARSSH_SSH_AUTHORIZED_KEYS",
			"value": ssh_keys.login_key_pub,
		},
		{
			"name": "FARSSH_SSH_HOST_RSA_KEY_BASE64",
			"value": base64.b64encode(bytes(ssh_keys.host_key, "utf-8")).decode("utf-8")
		}
	]

	override_entry = {
		"name": "farssh", # container name from task definition
		"environment": override_env,
	}

	overrides = {}
	overrides['containerOverrides'] = [ override_entry ]

	network_configuration = {
		"awsvpcConfiguration": {
			"subnets": args.public_subnets,
			"securityGroups": [ args.security_group ],
			"assignPublicIp": args.assign_public_ipv4,
		}
	}

	ecs = boto3.client('ecs')
	tasks = ecs.run_task(
		cluster = "farssh",
		capacityProviderStrategy = [
			{ "capacityProvider": "FARGATE", "weight": 1, "base": 1 },
			# { "capacityProvider": "FARGATE_SPOT", "weight": 0, "base": 0 }, # not supported for Arm images
		],
		taskDefinition = f"farssh-{farssh_id}",
		enableExecuteCommand = args.enable_execute_command,
		overrides = overrides,
		networkConfiguration = network_configuration,
	)

	task = tasks['tasks'][0]
	task_arn = task['taskArn']
	task_id = task_arn.split('/')[-1]

	print(f"Launched FarSSH ECS task: {task_id}")
	print(f"Status: {task['lastStatus']}")

	while True:
		time.sleep(1)

		task_old = task
		task = ecs.describe_tasks(cluster = "farssh", tasks = [ task_arn ])['tasks'][0]

		if task['lastStatus'] == "STOPPED":
			raise SystemExit("ERROR:  ECS task is in status STOPPED; see ECS Console for details.")

		if task['lastStatus'] != task_old['lastStatus']:
			print(f"Status: {task['lastStatus']}")

		if task['lastStatus'] == "RUNNING":
			break

	ip_address = select_ip_address(args, task)

	print(f"FarSSH task IP address: {ip_address}")
	print()

	return ip_address

def select_database(args):
	rds = boto3.client('rds')

	db_instances = rds.describe_db_instances()['DBInstances']
	db_clusters = rds.describe_db_clusters()['DBClusters']
	db_clusters_with_instances = [dbi.get('DBClusterIdentifier') for dbi in db_instances if dbi.get('DBClusterIdentifier')]

	available = []

	for candidate_instance in db_instances:
		available += [{
			'identifier': candidate_instance.get('DBInstanceIdentifier'),
			'cluster':    candidate_instance.get('DBClusterIdentifier'),
			'engine':     candidate_instance.get('Engine'),
			'status':     candidate_instance.get('DBInstanceStatus'),
			'hostname':   candidate_instance['Endpoint'].get('Address'),
			'port':       candidate_instance['Endpoint'].get('Port'),
			'database':   candidate_instance.get('DBName'),
			'username':   candidate_instance.get('MasterUsername'),
		}]

	for candidate_cluster in db_clusters:
		cluster_id = candidate_cluster.get('DBClusterIdentifier')

		# exclude clusters that also have associated instances
		if cluster_id in db_clusters_with_instances:
			continue

		available += [{
			'identifier': cluster_id,
			'cluster':    cluster_id,
			'engine':     candidate_instance.get('Engine'),
			'status':     candidate_cluster.get('Status'),
			'hostname':   candidate_cluster['Endpoint'],
			'port':       candidate_cluster.get('Port'),
			'database':   candidate_cluster.get('DatabaseName'),
			'username':   candidate_cluster.get('MasterUsername'),
		}]

	candidates = []
	for db in available:
		if db['status'] != "available":
			continue

		if args.cmd_args.get('command') == "psql" and "postgres" not in db['engine']:
			continue

		if args.cmd_args.get('command') == "mysql" and "mysql" not in db['engine'] and "maria" not in db['engine']:
			continue

		if args.cmd_args.get('identifier') and db['identifier'].lower() != args.cmd_args.get('identifier').lower():
			continue

		candidates += [db]

	if len(candidates) == 0:
		raise SystemExit("ERROR:  No matching database found")

	if len(candidates) == 1:
		db = candidates[0]
		if not args.cmd_args.get('identifier'):
			print(f"Selected database: {db['identifier']} ({db['hostname']})")
		return db

	print("Multiple databases available; use --identifier/-i to select one:")
	for db in candidates:
		print(f"- {db['identifier']}")

	exit(0)

