# FarSSH Testing Plan

This document outlines the manual testing procedures for FarSSH. All tests should be executed manually before each release.

## Prerequisites

### AWS Environment Setup
Before running tests, ensure you have:
- A deployed FarSSH CloudFormation stack in your test AWS account
- A test VPC with:
  - Public subnet with IPv6 enabled
  - RDS PostgreSQL instance (available)
  - RDS MySQL/MariaDB instance (optional)
  - Security groups configured to allow FarSSH connections

### Local Environment
```bash
# Set AWS credentials
export AWS_PROFILE=farssh-test
export AWS_REGION=eu-central-1

# Install FarSSH client
pip install -e ./client

# Verify installation
farssh --version
```

---

## Test Cases

### 1. SSH Mode
**Command:** `farssh ssh`

**Steps:**
1. Run `farssh ssh`
2. Verify SSH connection to VPC
3. Run a test command (e.g., `hostname`, `ip address`)
4. Exit the SSH session with `exit` or `Ctrl-D`

**Expected Result:** Interactive shell in VPC with working network connectivity

---

### 2. Proxy Mode (SOCKS)
**Command:** `farssh proxy`

**Steps:**
1. Run `farssh proxy`
2. Configure browser or application to use SOCKS proxy on `localhost:1080`
3. Verify browsing works through the VPC (check IP at whatismyip.com)
4. Terminate with `Ctrl-C`

**Expected Result:** SOCKS proxy available, traffic routed through VPC

---

### 3. Tunnel Mode
**Command:** `farssh tunnel 5432 <rds-host> 5432`

**Steps:**
1. Run `farssh tunnel 5432 <rds-postgresql-endpoint> 5432`
2. In another terminal: `psql -h localhost -p 5432 -U <username> -d <database>`
3. Run a test query (e.g., `SELECT 1;`)
4. Terminate tunnel with `Ctrl-C`

**Expected Result:** Local port 5432 forwards to RDS PostgreSQL endpoint

---

### 4. psql Mode (Direct)
**Command:** `farssh psql`

**Steps:**
1. Run `farssh psql` (or with `-U <username> <database>`)
2. Run a test query (e.g., `\dt`, `SELECT 1;`)
3. Exit with `\q` or `Ctrl-D`

**Expected Result:** Direct psql connection to RDS PostgreSQL instance

---

### 5. mysql Mode (Direct)
**Command:** `farssh mysql`

**Steps:**
1. Run `farssh mysql` (or with `-u <username> -p <database>`)
2. Run a test query (e.g., `SHOW DATABASES;`)
3. Exit with `exit` or `Ctrl-D`

**Expected Result:** Direct mysql connection to RDS MySQL/MariaDB instance

---

### 6. IPv6 Mode
**Command:** `farssh -6 ssh`

**Steps:**
1. Run `farssh -6 ssh`
2. Verify connection is established via IPv6
3. Run `ip address` and check for IPv6 address
4. Exit with `exit` or `Ctrl-D`

**Expected Result:** Connection via IPv6, SSH works over IPv6

---

### 7. Fargate Spot
**Command:** `farssh -S ssh`

**Steps:**
1. Run `farssh -S ssh`
2. Check ECS console to verify FARGATE_SPOT capacity provider is used
3. Exit with `exit` or `Ctrl-D`

**Expected Result:** ECS task uses FARGATE_SPOT capacity provider

---

### 8. Connection Cleanup
**Command:** Any connection mode

**Steps:**
1. Start a tunnel or connection
2. Establish a connection through it
3. Disrupt the connection so neither side has a chance to shut down the connection (pull cable / disconnect WiFi)
4. Wait 60+ seconds (idle timeout)
5. Check ECS console - task should be terminated

**Expected Result:** ECS task terminates after no active connections for ~60 seconds

---

### 9. Tunnel with Custom Local Port
**Command:** `farssh tunnel 9000 myhost.example.com 5432`

**Steps:**
1. Run tunnel with non-standard local port
2. Connect to localhost:9000
3. Verify connection routes to remote host

**Expected Result:** Local port 9000 forwards to remote host:5432

---

### 10. Multiple Commands via SSH
**Command:** `farssh ssh -- /bin/sh -c "echo test && hostname"`

**Steps:**
1. Run `farssh ssh -- /bin/sh -c "echo test && hostname"`
2. Verify output is displayed
3. Session should exit automatically

**Expected Result:** Commands executed remotely, output displayed, session ends

---

## Test Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| AWS_PROFILE | AWS credential profile | `farssh-test` |
| AWS_REGION | AWS region | `eu-central-1` |
| PGUSER | Default PostgreSQL username | `admin` |
| PGDATABASE | Default PostgreSQL database | `postgres` |

---

## Post-Release Verification

After each release, verify:
1. New version shows correctly: `farssh --version`
2. Docker image tag matches release version
3. All connection modes work as expected

---

## Known Limitations

- SSH session keeps alive while tunnel client runs (Ctrl-C required to terminate)
- Fargate Spot may take longer to provision than on-demand
- IPv6 requires VPC/subnet to have IPv6 CIDR block
