Le lancement de TiledViz se fait via le script `launch_TiledViz` qui démarre le script python `TVSecure.py`

Ce script permet, entre autres, de lancer des conteneurs de connexions.

Chaque conteneur a :

- Un port aléatoire sur lequel le démon `sshd` écoute.
- Une liste de ports aléatoires pour chaque tuile.

L'objectif est d'utiliser un pare-feu pour bloquer par défaut toutes les connexions entrantes et n'ouvrir dynamiquement que les ports nécessaires.

***

## Python-iptables

En recherchant "Python iptables" sur internet, je suis tombé sur la page officielle de PyPI proposant le module [`python-iptables`](https://pypi.org/project/python-iptables/). J'ai donc voulu le tester sur une machine virtuelle de test sous Rocky 8.

**Environnement de test :**  

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

Je fais un test simple : lister la table `filter` et ajouter une chaîne `TestChain`

```bash
(env)$ sudo /home/bilal/env/bin/python3
[sudo] Mot de passe de bilal :
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

Attention : il faut exécuter le module avec les privilèges root, sinon on obtient l'erreur suivante :

```bash
iptc.ip4tc.IPTCError: can't initialize filter: b'Permission denied (you must be root)'
```

Mais, en vérifiant avec `iptables -L`, la chaîne `TestChain` n’apparaît pas. Et il y a un warning qui indique l'utilisation de `iptables-legacy`.

```bash
[root]$ iptables -L | grep -i chain
# Warning: iptables-legacy tables present, use iptables-legacy to see them
Chain INPUT (policy ACCEPT)
Chain FORWARD (policy ACCEPT)
Chain OUTPUT (policy ACCEPT)
```

En tentant d'exécuter `iptables-legacy`, j'ai constaté qu'il n'était ni installé sur le système ni présent dans les dépôts :

```bash
[root]$ iptables-legacy
-bash: iptables-legacy : commande introuvable

[root]$ dnf search iptables-legacy
Aucune correspondance trouvée.
```

***

## `iptables`, `iptables-legacy` et `nftables`

En fouillant la [documentation](https://bugzilla.redhat.com/show_bug.cgi?id=1873474#c4) de Red Hat, j'ai trouvé cette phrase :

> "We are not going to include iptables-legacy in RHEL8. iptables (nftables or legacy) itself will be deprecated for RHEL9 as well, in preference to nftables."

Je me suis donc demandé qu'est ce que c'est `iptables-legacy`, `iptables-nft` et `nftables` ? 

Ce qui m'a amené à 2 supers docs :

- [netfilter](https://netfilter.org/)
- [developers.redhat.com](https://developers.redhat.com/blog/2020/08/18/iptables-the-two-variants-and-their-relationship-with-nftables)

Et voici ce que j'ai compris :

- `netfilter` est un projet qui permet au noyau Linux de filtrer les paquets.
- `iptables` est un outil de `netfilter` qui permet de définir des règles de filtrage.
	- Deux variantes d'`iptables` existent : `iptables-legacy` et `iptables-nft`.
- `nftables` est son successeur qui offre une plus grande flexibilité.
	- La commande `nft` est utilisée pour manipuler `nftables` avec une syntaxe différente de `iptables`.

Diagramme de fonctionnement :

```
+--------------+     +--------------+     +--------------+
|   iptables   |     |   iptables   |     |     nft      |   USER
|    legacy    |     |     nft      |     |  (nftables)  |   SPACE
+--------------+     +--------------+     +--------------+
       |                          |         |
====== | ===== KERNEL API ======= | ======= | =====================
       |                          |         |
+--------------+               +--------------+
|   iptables   |               |   nftables   |              KERNEL
|      API     |               |     API      |              SPACE
+--------------+               +--------------+
             |                    |         |
             |                    |         |
          +--------------+        |         |     +--------------+
          |   xtables    |--------+         +-----|   nftables   |
          |    match     |                        |    match     |
          +--------------+                        +--------------+
```

En vérifiant la version d'`iptables` sur ma VM, on comprend pourquoi il y a eu le warning.

```bash
$ iptables -V
iptables v1.8.5 (nf_tables)
```

Le module `iptables-python` doit se baser sur la variante `iptables-legacy`. La création de chaînes, règles, etc., avec `legacy` génère un avertissement et en invoquant `iptables-nft`, ces règles ne sont pas visibles.

En poursuivant mes recherches, je suis tombé sur une [documentation](https://docs.rockylinux.org/fr/guides/security/enabling_iptables_firewall/) de Rocky Linux : 

> "As of Rocky Linux 9.0, `iptables` and all of the utilities associated with it, are deprecated. This means that future releases of the OS will be removing `iptables`"

Avec ces informations, j'ai choisis d'utiliser `nftables` avec `nft`.

## Utilisation de `nftables` 

Je me suis basé sur cette [doc](https://ral-arturo.org/2020/11/22/python-nftables-tutorial.html).

Un module Python permet d'interagir avec `libnftables` *(bibliothèque pour interagir avec nftables)* via `ctypes` *(bibliothèque python pour interagir avec des bibliothèques écrites en C comme `libnftables`)*. 

Pour l'utiliser il faut installer le paquet `python3-nftables`, mais il est général installé par défaut avec Python :

```bash
[root]$ rpm -q python3-nftables
python3-nftables-1.0.4-7.el8_10.x86_64
```

(Il est aussi possible de l'installer via pip) :

```bash
pip install ansibleguy-nftables
```

Tout comme `python-iptables`, je test rapidement ce module :

```bash
$ sudo python3
[sudo] Mot de passe de bilal :
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

Je vérifie sur le terminal :

```bash
[root]$ nft list ruleset
table inet filter {
}
```

Tout fonctionne !

Le service `nftables` est géré par `systemd`, pour activer le pare-feu il faut lancer le service :

```bash
$ sudo systemctl start nftables.service
```

***

## Sécurisation de TiledViz

L'objectif est de bloquer par défaut toute les connexions entrantes et d'ouvrir dynamiquement les ports nécessaires.

Dans `launch_TiledViz.sh` je m'assure que le service `nftables` est actif :

```bash
# launch_TiledViz.sh
# Lance le service et l'active s'il ne l'est pas
(systemctl status nftables.service | grep -w active) || (sudo systemctl start nftables.service && sudo systemctl enable nftables.service)
```

Et j'exécute `TVSecure.py` avec les droits sudo :

```bash
# launch_TiledViz.sh
sudo python3 TVSecure/TVSecure.py --POSTGRES_HOST=${POSTGRES_HOST} --POSTGRES_IP=${POSTGRES_IP} --POSTGRES_PORT=${POSTGRES_PORT} \
        --POSTGRES_DB=${POSTGRES_DB} --POSTGRES_USER=${POSTGRES_USER} --POSTGRES_PASSWORD=${POSTGRES_PASSWORD} \
        --secretKey="$passwordFlask" 2>&1 \
    | grep -v "DEBUG:urllib3.*" | grep -v " :running" \
    | sed -e "s%TVSecure \([0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9] [0-9][0-9]:[0-9][0-9]:[0-9][0-9],[0-9][0-9][0-9]\) \- Thread\-\([0-9]*\) .* HTTP/1.1\" 200 None%\1 \2%" | grep -v " 1 " | grep -v 404
```

J'ajoute les règles `nftables` dans `TVSecure.py`

```python
# TVSecure/TVSecure.py
import nftables

nft = nftables.Nftables()

# Ferme tous les ports
nft.cmd("flush ruleset")
nft.cmd("add table inet filter")
nft.cmd("add chain inet filter INPUT { type filter hook input priority 0 ; policy drop ; }")

# Autorise les connexions établies et le DNS (pour ping et faire de requêtes internet)
nft.cmd("add rule inet filter INPUT ct state related,established accept")
nft.cmd("add rule inet filter INPUT udp dport 53 accept")
```

Dès que l'on récupère le port SSH, on l'ouvre :

```python
nft.cmd("add rule inet filter INPUT tcp dport " + str(PORTssh) + " accept")
```

À chaque ajout d'un port pour une tuile, on l'ouvre :

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
            # Ouvre le port
            nft.cmd("add rule inet filter INPUT tcp dport " + str(port) + " accept")
```

Voici un exemple de script complet pour tester :

```python
# test-TVSecure.py
import socket
import nftables

nbTiles = 10

# Ferme les ports
nft = nftables.Nftables()
nft.cmd("flush ruleset")
nft.cmd("add table inet filter")
nft.cmd("add chain inet filter INPUT { type filter hook input priority 0 ; policy drop ; }")

# Pour moi
nft.cmd("add rule inet filter INPUT tcp dport 22 accept")

# Pour continuer à pouvoir ping et faire les requetes DNS
nft.cmd("add rule inet filter INPUT ct state related,established accept")
nft.cmd("add rule inet filter INPUT udp dport 53 accept")

# Récupère un port libre pour ssh
s=socket.socket()
s.bind(('', 0))
PORTssh = s.getsockname()[1]
s.close()

# Ouvre le port SSH
nft.cmd("add rule inet filter INPUT tcp dport "+str(PORTssh)+" accept")

# Ports for tiles
listPortsTiles = {str(PORTssh)+'/tcp':('0.0.0.0',PORTssh)}
listPorts = [PORTssh]
listSock = []

# Prends un nombre de port égale au nombre de Tiles
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
            # Ouvre le port
            nft.cmd("add rule inet filter INPUT tcp dport "+str(port)+" accept")
            
        else:
            # Ferme la socket non utilisée
            s.close()  


print("Build connection with "+str(nbTiles + 1)+" ports : "+str(listPortsTiles))
print("ssh port : "+ str(PORTssh))



rc, output, error = nft.cmd("list ruleset")
print(output)

# Ferme toutes les sockets à la fin
for s in listSock:
    s.close()
```

```bash
# test-launch_TiledViz.sh
#!/bin/bash

# Démarre le service nftables si nécessaire
(systemctl status nftables.service | grep -w active) || (sudo systemctl start nftables.service && sudo systemctl enable nftables.service)

# Exécute le script Python
sudo python3 test-TVSecure.py
```

### Tests de validation

**Avant l'exécution du script**

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

On peut accéder à n'importe quel port qu'on ouvre

```bash
bg281242@mdlspc178:~$ nc -Nv 192.168.56.106 1234
Connection to 192.168.56.106 1234 port [tcp/*] succeeded!
```

**Après l'exécution du script**

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

On ne peut plus accéder à n'importe quel port et le service nftables est activé.

Mais on peut accéder au ports qu'on a ouvert (comme le 39683)

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

***

## Améliorations apportées

En mettant en place cette solution, nous avons rencontré trois problèmes :

1. L'utilisation de sudo pour lancer le script Python créait des problèmes de permissions dans toute l'arborescence de TiledViz
2. D'autres règles Docker étaient présentes, donc faire un `flush ruleset` à l'exécution de `launch_TiledViz` les supprimait
3. Le service nftables.service géré par systemd lance `/etc/sysconfig/nftables.conf` qui est commenté en entier par défaut, donc que le service soit actif ou non ne changeait rien

Il fallait trouver une solution pour manipuler les règles de pare-feu sans avoir tous les droits root. C'est exactement ce que les capabilities Linux permettent !

### Capabilities Linux

Traditionnellement dans UNIX, il existe deux catégories de processus : privilégiés et non privilégiés.

- Les processus privilégiés contournent toutes les vérifications de permission du noyau
- Les processus non privilégiés voient leurs permissions vérifiées en fonction de leur UID et GID effectifs

À partir du noyau 2.2, Linux a divisé les privilèges associés à root en plusieurs unités appelées capabilities.

Dans notre cas, `CAP_NET_ADMIN` est la capacité qui nous intéresse. Voici sa description dans le man 7 capabilities  :

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

Ces capacités s'appliquent sur des fichiers binaires. Dans le cas de TVSecure.py qui est lancé via python3, il faut les appliquer sur le fichier binaire de Python.

### Modifications dans install.sh

Nous avons ajouté un paramètre `security` que l'utilisateur peut positionner à `y` ou `n` :

- Si activé, on décommente les lignes ajoutées dans TVSecure qui créent le pare-feu
- On active la capability sur le Python du système (en utilisant `realpath` et `which` pour trouver le bon chemin) :

```bash
sudo setcap cap_net_admin=eip $(realpath $(which python))
```

### Modifications dans envTiledViz

Nous avons ajouté la variable d'environnement `SECURITY` qui sera modifiée par install.sh.

### Modifications dans TVSecure.py

Au lieu de créer une chaîne INPUT qui peut porter à confusion, nous créons une chaîne spécifique `TILEDVIZ` (dans le main du script à la fin, et non au début lorsqu’on fait les import et les définitions de variable) :

```python
nft.cmd("add chain ip filter TILEDVIZ { type filter hook input priority 0 ; policy drop ; }")
```

Avant de créer une chaîne, nous la vidons pour éviter les règles redondantes (la distinction entre destroy et delete est importante):

```python
nft.cmd("destroy chain ip filter TILEDVIZ")
```

Pour chaque conteneur de connexion qui active la méthode `run`, nous créons une nouvelle chaîne et on insère un `jump` vers cette chaîne dans la chaîne TILEDVIZ :

```python
nft.cmd("add chain ip filter " + str(self.name))
nft.cmd("add rule ip filter TILEDVIZ jump " + str(self.name))
```

Cette approche permet de facilement supprimer toutes les règles en même temps que le conteneur en "détruisant" (destroy) sa chaîne.

Nous gérons également les signaux d'interruption (CTRL+C) pour nettoyer les règles si l'utilisateur arrête le programme : 

```python
def signal_handler(sig, frame):
    nft.cmd("destroy chain ip filter TILEDVIZ")
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)
```
