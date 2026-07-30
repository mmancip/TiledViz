\page md_TiledViz_Installation TiledViz Installation


# TiledViz Installation
# Installation
To install TiledViz you will need to first get the [latest release](https://github.com/mmancip/TiledViz/releases) available on github.
## Preparing the environment
For the host part, named **TiledViz Secure**, you need to install:

- `python3`
- `pip3`, usually provided by the `python3-pip` package
- `libcap-dev`
- `docker.io`
- `docker-buildx`

*Please note that name may differ depending on your OS*

### 1. Docker rights
You must first install Docker.
Required Docker version:
```text
17.03 or newer
```
You must be in the `docker` group to be able to launch Docker containers.
```bash 
sudo usermod -aG docker $USER
```
After adding your user to the `docker` group, **log out and log back in**. 
Then check with:
```bash
id
```
*No TiledViz containers are executed with root users for security reasons.*


### 2. PostgreSQL environment

The PostgreSQL service is downloaded from DockerHub with an Alpine system.

If you need several `postgres-alpine` Docker containers running, you can change the PostgreSQL port in `./envTiledViz` before installation.

The `./envTiledViz` file is private because it stores the PostgreSQL password for the PostgreSQL service.

### 3. TVSecure parameters in tiledviz.conf

You may change the values in `tiledviz.conf` before installation.

Important parameters:

| Parameter | Description |
|---|---|
| `NbSecureConnection` | Number of thread pool for TVSecure. |
| `ConnectionPort` | Port used for connections to TiledViz intermediate Docker containers and HPC machines. |
| `ActionPort` | Port used for actions between TiledViz intermediate Docker containers and HPC machines. |

### 4. SMTP relay in connection Docker image, if needed

The installation builds the connection Docker image if you want to launch connection containers.
If you want to use automatic email in your scripts, add the SMTP server parameter in:
```text
TVConnections/mageianconnect/Dockerfile
```
Replace:
```text
TODO_SMTP
```
with the SMTP server IP address.

Use the **IP address** because DNS may not work inside the container.

### 5. SSH parameters

On the web server, the SSH daemon configuration must contain:
```text
GatewayPorts yes
```
Make sure this line is uncommented in the SSH daemon configuration file.
After modifying the SSH daemon configuration, restart the SSH service if needed.

## Installation command
During the installation you will need to answer several prompts :
- Activate firewallT
 *Allow dynamic port*
- PostgreSQL database password
- SERVER.DOMAIN
  *Where TiledViz will be accessible*
- Public SSL key path
- Private SSL key path
- SMTP *This is necessary for the 2FA verification.*
	- Server address
	- Port address
	- SSL option
	- TLS option
	- Username *usually same as email*
	-  Password
	- The "from" email 

- IMAP server and port address
- NTP server address

Once all configuration points and variables are checked, run:
```bash
./install.sh > install.log 2>&1
```
The installation log will be written to:
```text
./install.log
```
During the installation
The installation creates the following directory:
```bash
$HOME/.tiledviz
```
There are two configuration files:
- `envTiledViz`

- `tiledviz.conf`
*You may need to edit this file before installation.*
### envTiledViz

`envTiledViz` contains the PostgreSQL parameters and the Python 3 virtual environment configuration.

It will be filled in:
```bash
${HOME}/.cache/envTiledViz
```
This file is private because it keeps the PostgreSQL password for the PostgreSQL service.

The virtual environment directory will be named:
```text
TiledVizEnv_${DATE}
```
where `${DATE}` is the installation date saved in `envTiledViz`.
### tiledviz.conf

`tiledviz.conf` will be copied into:
```bash
${HOME}/.tiledviz
```
