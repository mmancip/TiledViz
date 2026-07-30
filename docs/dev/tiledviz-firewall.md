\page md_tiledviz-firewall TiledViz FireWallT


# TiledViz FireWallT

TiledViz is launched via the `launch_TiledViz` script, which starts the `TVSecure.py` Python script.

Among other things, this script launches connection containers.

Each container has:

* A random port on which the `sshd` daemon listens.
* A list of random ports for each tile.

The goal is to use a firewall to block all incoming connections by default and dynamically open only the necessary ports.

---

## Python-iptables

Searching for "Python iptables" on the internet, I found the official PyPI page offering the [`python-iptables`](https://pypi.org/project/python-iptables/) module. I decided to test it on a test virtual machine running Rocky 8.

**Test environment:**

```bash
$ hostnamectl
Operating System: Rocky Linux 8.10 (Green Obsidian)
Kernel: Linux 4.18.0-553.40.1.el8_10.x86_64

$ python3 --version
Python 3.6.8
```

```bash
(env)$ pip install python-iptables
Collecting python-iptables
Using cached https://files.pythonhosted.org/.../python-iptables-1.0.1.tar.gz
Installing collected packages: python-iptables
Running setup.py install for python-iptables ... done
Successfully installed python-iptables-1.0.1
```

I ran a simple test: listing the `filter` table and adding a `TestChain` chain.

```bash
(env)$ sudo /home/bilal/env/bin/python3
[sudo] password for bilal:
Python 3.6.8 (default, Dec  4 2024, 12:35:02)
[GCC 8.5.0 20210514 (Red Hat 8.5.0-22)] on linux
>>> import iptc
>>> iptc.easy.dump_table('filter')
{'INPUT': [], 'FORWARD': [], 'OUTPUT': []}
>>> iptc.easy.add_chain('filter', 'TestChain')
True
>>> iptc.easy.dump_table('filter')
{'INPUT': [], 'FORWARD': [], 'OUTPUT': [], 'TestChain': []}
```

Note: the module must be executed with root privileges, otherwise the following error occurs:

```bash
iptc.ip4tc.IPTCError: cant initialize filter: Permission denied (you must be root)
```

However, checking with `iptables -L`, the `TestChain` chain does not appear. There is also a warning indicating the use of `iptables-legacy`.

```bash
[root]$ iptables -L | grep -i chain
# Warning: iptables-legacy tables present, use iptables-legacy to see them
Chain INPUT (policy ACCEPT)
Chain FORWARD (policy ACCEPT)
Chain OUTPUT (policy ACCEPT)
```

When attempting to run `iptables-legacy`, I noticed it was neither installed on the system nor available in the repositories:

```bash
[root]$ iptables-legacy
-bash: iptables-legacy: command not found

[root]$ dnf search iptables-legacy
No match found.
```

---

## `iptables`, `iptables-legacy`, and `nftables`

Digging through the Red Hat [documentation](https://bugzilla.redhat.com/show_bug.cgi?id=1873474#c4), I found this sentence:

> "We are not going to include iptables-legacy in RHEL8. iptables (nftables or legacy) itself will be deprecated for RHEL9 as well, in preference to nftables."

I then wondered what `iptables-legacy`, `iptables-nft`, and `nftables` were.

This led me to 2 great resources:

* [netfilter](https://netfilter.org/)
* [developers.redhat.com](https://developers.redhat.com/blog/2020/08/18/iptables-the-two-variants-and-their-relationship-with-nftables)

Here is what I understood:

* `netfilter` is a project that allows the Linux kernel to filter packets.
* `iptables` is a `netfilter` tool used to define filtering rules.
* Two variants of `iptables` exist: `iptables-legacy` and `iptables-nft`.


* `nftables` is its successor, offering greater flexibility.
* The `nft` command is used to manipulate `nftables` with a different syntax than `iptables`.



Operation diagram:

```
+--------------+     +--------------+     +--------------+
|   iptables   |     |   iptables   |     |      nft     |   USER
|    legacy    |     |      nft     |     |  (nftables)  |   SPACE
+--------------+     +--------------+     +--------------+
       |                          |         |
====== | ===== KERNEL API ======= | ======= | =====================
       |                          |         |
+--------------+               +--------------+
|   iptables   |               |   nftables   |              KERNEL
|     API      |               |     API      |              SPACE
+--------------+               +--------------+
             |                    |         |
             |                    |         |
          +--------------+        |         |     +--------------+
          |   xtables    |--------+         +-----|   nftables   |
          |    match     |                        |    match     |
          +--------------+                        +--------------+

```

Checking the `iptables` version on my VM explains why the warning appeared.

```bash
$ iptables -V
iptables v1.8.5 (nf_tables)
```

The `iptables-python` module must rely on the `iptables-legacy` variant. Creating chains, rules, etc., with `legacy` generates a warning, and when invoking `iptables-nft`, these rules are not visible.

Continuing my research, I came across Rocky Linux [documentation](https://docs.rockylinux.org/fr/guides/security/enabling_iptables_firewall/):

> "As of Rocky Linux 9.0, `iptables` and all of the utilities associated with it, are deprecated. This means that future releases of the OS will be removing `iptables`"

With this information, I chose to use `nftables` with `nft`.

## Using `nftables`

I based my work on this [doc](https://ral-arturo.org/2020/11/22/python-nftables-tutorial.html).

A Python module allows interacting with `libnftables` *(a library to interact with nftables)* via `ctypes` *(a Python library to interact with C libraries like `libnftables`)*.

To use it, the `python3-nftables` package must be installed, but it is generally installed by default with Python:

```bash
[root]$ rpm -q python3-nftables
python3-nftables-1.0.4-7.el8_10.x86_64
```

(It can also be installed via pip):

```bash
pip install ansibleguy-nftables
```

Just like `python-iptables`, I quickly tested this module:

```bash
$ sudo python3
[sudo] password for bilal:
Python 3.6.8 (default, Dec  4 2024, 12:35:02) 
[GCC 8.5.0 20210514 (Red Hat 8.5.0-22)] on linux
>>> import nftables
>>> nft = nftables.Nftables()
>>> nft.cmd("flush ruleset")
(0, '', '')
>>> nft.cmd("add table inet filter")
(0, '', '')
>>> nft.cmd("list ruleset")
(0, 'table inet filter {\n}\n', '')
```

I checked in the terminal:

```bash
[root]$ nft list ruleset
table inet filter {
}
```

Everything works!

The `nftables` service is managed by `systemd`; to enable the firewall, the service must be started:

```bash
$ sudo systemctl start nftables.service
```

---

## Securing TiledViz

The goal is to block all incoming connections by default and dynamically open the necessary ports.

In `launch_TiledViz.sh`, I ensure the `nftables` service is active:

```bash
# launch_TiledViz.sh
# Starts the service and enables it if it isn't already
(systemctl status nftables.service | grep -w active) || (sudo systemctl start nftables.service && sudo systemctl enable nftables.service)
```

And I run `TVSecure.py` with sudo privileges:

```bash
# launch_TiledViz.sh
sudo python3 TVSecure/TVSecure.py --POSTGRES_HOST=${POSTGRES_HOST} --POSTGRES_IP=${POSTGRES_IP} --POSTGRES_PORT=${POSTGRES_PORT} \
        --POSTGRES_DB=${POSTGRES_DB} --POSTGRES_USER=${POSTGRES_USER} --POSTGRES_PASSWORD=${POSTGRES_PASSWORD} \
        --secretKey="$passwordFlask" 2>&1 \
    | grep -v "DEBUG:urllib3.*" | grep -v " :running" \
    | sed -e "s%TVSecure \([0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9] [0-9][0-9]:[0-9][0-9]:[0-9][0-9],[0-9][0-9][0-9]\) \- Thread\-\([0-9]*\) .* HTTP/1.1\" 200 None%\1 \2%" | grep -v " 1 " | grep -v 404
```

I add the `nftables` rules in `TVSecure.py`

```python
# TVSecure/TVSecure.py
import nftables

nft = nftables.Nftables()

# Closes all ports
nft.cmd("flush ruleset")
nft.cmd("add table inet filter")
nft.cmd("add chain inet filter INPUT { type filter hook input priority 0 ; policy drop ; }")

# Allows established connections and DNS (for ping and internet requests)
nft.cmd("add rule inet filter INPUT ct state related,established accept")
nft.cmd("add rule inet filter INPUT udp dport 53 accept")
```

As soon as the SSH port is retrieved, it is opened:

```python
nft.cmd("add rule inet filter INPUT tcp dport " + str(PORTssh) + " accept")
```

Each time a port is added for a tile, it is opened:

```python
for i in range(nbTiles):
    already = True
    
    while already:
        s = socket.socket()
        s.bind(('', 0))
        port = s.getsockname()[1]
        
        if port not in listPorts:
            already = False
            listPorts.append(port)
            listSock.insert(0, s)
            listPortsTiles[str(port) + '/tcp'] = ('0.0.0.0', port)
            # Opens the port
            nft.cmd("add rule inet filter INPUT tcp dport " + str(port) + " accept")
```

Here is an example of a complete script for testing:

```python
# test-TVSecure.py
import socket
import nftables

nbTiles = 10

# Close ports
nft = nftables.Nftables()
nft.cmd("flush ruleset")
nft.cmd("add table inet filter")
nft.cmd("add chain inet filter INPUT { type filter hook input priority 0 ; policy drop ; }")

# For me
nft.cmd("add rule inet filter INPUT tcp dport 22 accept")

# To continue being able to ping and make DNS requests
nft.cmd("add rule inet filter INPUT ct state related,established accept")
nft.cmd("add rule inet filter INPUT udp dport 53 accept")

# Retrieves a free port for ssh
s=socket.socket()
s.bind(('', 0))
PORTssh = s.getsockname()[1]
s.close()

# Opens the SSH port
nft.cmd("add rule inet filter INPUT tcp dport "+str(PORTssh)+" accept")

# Ports for tiles
listPortsTiles = {str(PORTssh)+'/tcp':('0.0.0.0',PORTssh)}
listPorts = [PORTssh]
listSock = []

# Takes a number of ports equal to the number of Tiles
for i in range(nbTiles):
    already=True

    while (already):
        s = socket.socket()
        s.bind(('', 0))
        port = s.getsockname()[1]

        if (not port in listPorts):
            already = False
            listPorts.append(port)
            listSock.insert(0,s)
            listPortsTiles[str(port)+'/tcp']=('0.0.0.0',port)
            # Opens the port
            nft.cmd("add rule inet filter INPUT tcp dport "+str(port)+" accept")
            
        else:
            # Closes the unused socket
            s.close()  


print("Build connection with "+str(nbTiles + 1)+" ports : "+str(listPortsTiles))
print("ssh port : "+ str(PORTssh))



rc, output, error = nft.cmd("list ruleset")
print(output)

# Closes all sockets at the end
for s in listSock:
    s.close()

```

```bash
# test-launch_TiledViz.sh
#!/bin/bash

# Starts the nftables service if necessary
(systemctl status nftables.service | grep -w active) || (sudo systemctl start nftables.service && sudo systemctl enable nftables.service)

# Executes the Python script
sudo python3 test-TVSecure.py

```

### Validation Tests

**Before script execution**

```bash
[bilal@localhost]$ systemctl status nftables.service
● nftables.service - Netfilter Tables
   Loaded: loaded (/usr/lib/systemd/system/nftables.service; enabled; vendor preset: disabled)
   Active: inactive (dead) since Tue 2025-02-18 11:21:04 CET; 33min ago

[bilal@localhost]$ nc -lv 1234
Ncat: Version 7.92 ( https://nmap.org/ncat )
Ncat: Listening on :::1234
Ncat: Listening on 0.0.0.0:1234

```

We can access any opened port:

```bash
bg281242@mdlspc178:~$ nc -Nv 192.168.56.106 1234
Connection to 192.168.56.106 1234 port [tcp/*] succeeded!

```

**After script execution**

```bash
[bilal@localhost]$ ./test-launch_TiledViz.sh
Build connection with 11 ports : {'39683/tcp': ('0.0.0.0', 39683), '58853/tcp': ('0.0.0.0', 58853), '45277/tcp': ('0.0.0.0', 45277), '44101/tcp': ('0.0.0.0', 44101), '53359/tcp': ('0.0.0.0', 53359), '44049/tcp': ('0.0.0.0', 44049), '42279/tcp': ('0.0.0.0', 42279), '34945/tcp': ('0.0.0.0', 34945), '48855/tcp': ('0.0.0.0', 48855), '45223/tcp': ('0.0.0.0', 45223), '56289/tcp': ('0.0.0.0', 56289)}
ssh port : 39683
table inet filter {
        chain INPUT {
                type filter hook input priority filter; policy drop;
                tcp dport 22 accept
                ct state established,related accept
                udp dport 53 accept
                tcp dport 39683 accept
                tcp dport 58853 accept
                tcp dport 45277 accept
                tcp dport 44101 accept
                tcp dport 53359 accept
                tcp dport 44049 accept
                tcp dport 42279 accept
                tcp dport 34945 accept
                tcp dport 48855 accept
                tcp dport 45223 accept
                tcp dport 56289 accept
        }
}

[bilal@localhost]$ systemctl status nftables.service
● nftables.service - Netfilter Tables
   Loaded: loaded (/usr/lib/systemd/system/nftables.service; enabled; vendor preset: disabled)
   Active: active (exited) since Tue 2025-02-18 11:56:18 CET; 4min 52s ago

[bilal@localhost]$ nc -lv 1234
Ncat: Version 7.92 ( https://nmap.org/ncat )
Ncat: Listening on :::1234
Ncat: Listening on 0.0.0.0:1234

```

We can no longer access just any port, and the nftables service is activated.

But we can access the ports we opened (like 39683):

```bash
[bilal@localhost]$ nc -lv 39683
Ncat: Version 7.92 ( https://nmap.org/ncat )
Ncat: Listening on :::39683
Ncat: Listening on 0.0.0.0:39683

```

```bash
bg281242@mdlspc178:~$ nc -Nv 192.168.56.106 39683
Connection to 192.168.56.106 39683 port [tcp/*] succeeded!

```

---

## Improvements Made

While implementing this solution, we encountered three problems:

1. Using sudo to launch the Python script created permission issues throughout the TiledViz directory tree.
2. Other Docker rules were present, so performing a `flush ruleset` when executing `launch_TiledViz` deleted them.
3. The nftables.service managed by systemd runs `/etc/sysconfig/nftables.conf`, which is entirely commented out by default, meaning whether the service was active or not made no difference.

We had to find a solution to manipulate firewall rules without needing full root privileges. This is exactly what Linux capabilities provide!

### Linux Capabilities

Traditionally in UNIX, there are two categories of processes: privileged and unprivileged.

* Privileged processes bypass all kernel permission checks.
* Unprivileged processes have their permissions checked based on their effective UID and GID.

Starting with kernel 2.2, Linux divided the privileges associated with root into several distinct units known as capabilities.

In our case, `CAP_NET_ADMIN` is the capability we are interested in. Here is its description in the `capabilities(7)` man page:

```
CAP_NET_ADMIN
              Perform various network-related operations:
              • interface configuration;
              • administration of IP firewall, masquerading, and accounting;
              • modify routing tables;
              • bind to any address for transparent proxying;
              • set type-of-service (TOS);
              • clear driver statistics;
              • set promiscuous mode;
              • enabling multicasting;
              • use setsockopt(2) to set the following socket options: SO_DEBUG, SO_MARK, SO_PRIORITY (for a priority outside the range 0 to 6), SO_RCVBUFFORCE, and SO_SNDBUFFORCE.

```

These capabilities apply to binary files. In the case of TVSecure.py, which is launched via python3, we need to apply them to the Python binary file.

### Modifications in install.sh

We added a `security` parameter that the user can set to `y` or `n`:

* If enabled, we uncomment the lines added in TVSecure that create the firewall.
* We enable the capability on the system's Python (using `realpath` and `which` to find the correct path):

```bash
sudo setcap cap_net_admin=eip $(realpath $(which python))

```

### Modifications in envTiledViz

We added the `SECURITY` environment variable, which will be modified by install.sh.

### Modifications in TVSecure.py

Instead of creating an INPUT chain which can be confusing, we create a specific `TILEDVIZ` chain (in the main part of the script at the end, not at the beginning during imports and variable definitions):

```python
nft.cmd("add chain ip filter TILEDVIZ { type filter hook input priority 0 ; policy drop ; }")

```

Before creating a chain, we flush it to avoid redundant rules (the distinction between destroy and delete is important):

```python
nft.cmd("destroy chain ip filter TILEDVIZ")

```

For each connection container that activates the `run` method, we create a new chain and insert a `jump` to this chain inside the TILEDVIZ chain:

```python
nft.cmd("add chain ip filter " + str(self.name))
nft.cmd("add rule ip filter TILEDVIZ jump " + str(self.name))

```

This approach allows easily removing all rules at the same time as the container by "destroying" its chain.

We also handle interrupt signals (CTRL+C) to clean up the rules if the user stops the program:

```python
def signal_handler(sig, frame):
    nft.cmd("destroy chain ip filter TILEDVIZ")
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)
```
