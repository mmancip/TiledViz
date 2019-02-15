#!/bin/sh
BASE_DIR=/etc/ssh

ssh-keygen -A

for item in dsa rsa ecdsa ed25519; do
    echo ">>> Fingerprints for ${item} host key"
    ssh-keygen -E md5 -lf ${BASE_DIR}/ssh_host_${item}_key
    ssh-keygen -E sha256 -lf ${BASE_DIR}/ssh_host_${item}_key
    ssh-keygen -E sha512 -lf ${BASE_DIR}/ssh_host_${item}_key
done
#/usr/sbin/sshd -D -f /etc/ssh/sshd_config &

mylogin=$1
mypassword=$2
myuid=$3

adduser  -D -u ${myuid} ${mylogin}

python change_pwd.py ${mylogin} ${mypassword}

/usr/sbin/sshd -D -f /etc/ssh/sshd_config
#su - ${mylogin}

