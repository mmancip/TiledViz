#!/bin/bash

# Test Docker rights
docker ps -a

# Build Virtualenv for TVSecure
if [ X"$1" == X"" ]; then
    echo "==== Build Virtualenv for TVSecure ===="
    export DATE=$(date +%F_%H-%M-%S)
    echo "DATE=$DATE"
    mkdir TiledVizEnv_${DATE}
    python3 -m venv TiledVizEnv_${DATE}
    source TiledVizEnv_${DATE}/bin/activate

    echo "==== Copy TiledViz env in .cache ===="
    [ ! -d $HOME/.cache ] && mkdir $HOME/.cache
    sed -e "s&DATE=.*&DATE=$DATE&" envTiledViz > $HOME/.cache/envTiledViz
    chmod 600 $HOME/.cache/envTiledViz

    ls -la $HOME/.cache/envTiledViz
    source $HOME/.cache/envTiledViz
else
    OLDENV=$(find . -maxdepth 1 -type d -name "TiledVizEnv_*" |tail -1)
    export DATE_ENV=$(echo $OLDENV |sed -e 's&\./TiledVizEnv_&&')
    source $OLDENV/bin/activate

    ls -la $HOME/.cache/envTiledViz
    source $HOME/.cache/envTiledViz
    if [ ${DATE_ENV} != ${DATE} ]; then
	echo "Error restart install : DATEs not equal ${DATE_ENV} != ${DATE}."
	exit 1
    fi
fi

echo "===== Enable FirewallT Tiledviz ====="
# Améliorer clean input ?
echo "Activate firewallT for Tiledviz ? : ('n' or 'y')"
read -s firewallT;
[[ $firewallT == y || $firewallT == n ]] && echo "Valid Input" || echo "Invalid Input"

echo "==== Install environment ===="
# pre-version 3.0 sqlacodegen
pip3 install --pre sqlacodegen
# other packages
pip3 install -r requirements.txt

# Get noVNC
echo "==== Get noVNC ===="
pushd TVWeb
git clone https://github.com/novnc/noVNC.git noVNC
cd noVNC
git checkout v1.4.0
patch -p0 < ../patch_ui
cd ..
cp vnc_multi.html noVNC
cp ui_multi.js noVNC/app
cp rfb_multi.js noVNC/core
#patch -p0 < patch_devices_noVNC 
popd

echo "==== Get websockify ===="
pushd TVConnections
git clone https://github.com/novnc/websockify
popd

# Launch postgresql docker
echo "==== Launch postgresql docker ===="
if ( $installX11 ); then
    password=$(python3 -c "import zenipy; password=zenipy.zenipy.password(title='PostgreSQL password',text='Please give a password for your postgresql DB : (no '@' or '/' !)', width=450, height=120, timeout=None); print(str(password))")
else
    echo "Please give a password for your postgresql DB : (no '@' or '/' !)"
    read -s password
fi
replpass=$( echo $password | sed -e "s|\&|\\\&|g" )
sed -e "s|your_postgres_password|$replpass|" -i $HOME/.cache/envTiledViz

echo "==== Copy tiledViz.conf in $HOME/.tiledviz cache dir ===="
mkdir $HOME/.tiledviz
cp tiledviz.conf $HOME/.tiledviz
[[ $firewallT == y ]] && sed -e "s|FirewallT=False|FirewallT=True|" -i $HOME/.tiledviz/tiledviz.conf 


echo "=== Add SSL certificates ==="
if ( $installX11 ); then
    myweb=$(python3 -c "import zenipy; myweb=zenipy.zenipy.password(title='SSL web server.domain name',text='Please give a SERVER.DOMAIN for your SSL web server.', width=450, height=120, timeout=None); print(str(myweb))")
else
    echo "Please give a SERVER.DOMAIN for your SSL web server"
    read myweb;
fi
IFS='.' read -r -a webline <<<$myweb

# Array slice
serv="${webline[@]: 0:$((${#webline[*]}-2))}"
SERVER_NAME=$(echo $serv |sed -e "s/ /./g")
DOMAIN=${webline[${#webline[*]}-2]}.${webline[${#webline[*]}-1]}


if ( $installX11 ); then
    SSLpublic=$(python3 -c "import zenipy; myssl=zenipy.zenipy.password(title='SSL PUBLIC key path',text='Please give the PUBLIC SSL key PATH.', width=450, height=120, timeout=None); print(str(myssl))")
    SSLprivate=$(python3 -c "import zenipy; myssl=zenipy.zenipy.password(title='SSL PRIVATE key path',text='Please give the PRIVATE SSL key PATH.', width=450, height=120, timeout=None); print(str(myssl))")
    SMTP_SERVER=$(python3 -c "import zenipy; myserver=zenipy.zenipy.password(title='SMTP server address',text='Please give your SMTP server address - the outgoing mail server.', width=450, height=120, timeout=None); print(str(myserver))")
    SMTP_PORT=$(python3 -c "import zenipy; myport=zenipy.zenipy.password(title='SMTP server PORT',text='Please give your SMTP server address - for the outgoing mail server.', width=450, height=120, timeout=None); print(str(myport))")
    SMTP_USE_SSL=$(python3 -c "import zenipy; myssl=zenipy.zenipy.password(title='SMTP server SSL option',text='Please give your SSL option - for the outgoing mail server.', width=450, height=120, timeout=None); print(str(myssl))")
    SMTP_USE_TLS=$(python3 -c "import zenipy; mytls=zenipy.zenipy.password(title='SMTP server TLS option',text='Please give your TLS option - for the outgoing mail server.', width=450, height=120, timeout=None); print(str(mytls))")
    SMTP_USERNAME=$(python3 -c "import zenipy; myuser=zenipy.zenipy.password(title='SMTP user name',text='Please give your user name - for the outgoing mail server.', width=450, height=120, timeout=None); print(str(myuser))")
    SMTP_PASSWORD=$(python3 -c "import zenipy; mypass=zenipy.zenipy.password(title='SMTP password',text='Please give your password - for the outgoing mail server.', width=450, height=120, timeout=None); print(str(mypass))")
    FROM_EMAIL=$(python3 -c "import zenipy; myuser=zenipy.zenipy.password(title='TiledViz email',text='Please give this TiledViz email - for the outgoing mail server.', width=450, height=120, timeout=None); print(str(myuser))")
    IMAP_SERVER=$(python3 -c "import zenipy; myserver=zenipy.zenipy.password(title='IMAP server address',text='Please give your IMAP server address - the ingoing mail server.', width=450, height=120, timeout=None); print(str(myserver))")
    IMAP_PORT=$(python3 -c "import zenipy; myport=zenipy.zenipy.password(title='IMAP server PORT',text='Please give your IMAP server address - for the ingoing mail server.', width=450, height=120, timeout=None); print(str(myport))")


    NTP=$(python3 -c "import zenipy; myserver=zenipy.zenipy.password(title='NTP server address',text='Please give your NTP server address - the time server.', width=450, height=120, timeout=None); print(str(myserver))")
else
    echo "Please give the PUBLIC SSL key PATH."
    read SSLpublic;
    echo "Please give the PRIVATE SSL key PATH."
    read SSLprivate;

    echo "Please give your SMTP server address - the outgoing mail server."
    read SMTP_SERVER;
    echo "Please give your SMTP PORT address - for the outgoing mail server."
    read SMTP_PORT;
    echo "Please give your SMTP SSL option - for the outgoing mail server."
    read SMTP_USE_SSL;
    echo "Please give your SMTP TLS option - for the outgoing mail server."
    read SMTP_USE_TLS;
    echo "Please give your SMTP user name - for the outgoing mail server."
    read SMTP_USERNAME;
    echo "Please give your SMTP password - for the outgoing mail server."
    read SMTP_PASSWORD;
    echo "Please give this TiledViz email - for the outgoing mail server."
    read FROM_EMAIL;
    echo "Please give your IMAP server address - the ingoing mail server."
    read IMAP_SERVER;
    echo "Please give your IMAP PORT address - for the ingoing mail server."
    read IMAP_PORT;

    echo "Please give your NTP server address - the time server."
    read NTP;
fi

sed -e "s&_SERVER_NAME_&$SERVER_NAME&" \
    -e "s&_DOMAIN_&$DOMAIN&" \
    -e "s&_SSLpublic_&$SSLpublic&" \
    -e "s&_SSLprivate_&$SSLprivate&" \
    -e "s&_NTP_&$NTP&"  \
    -e "s&_SMTP_SERVER_&$SMTP_SERVER&" \
    -e "s&_SMTP_PORT_&$SMTP_PORT&" \
    -e "s&_SMTP_USE_TLS_&$SMTP_USE_TLS&" \
    -e "s&_SMTP_USE_SSL_&$SMTP_USE_SSL&" \
    -e "s&_SMTP_USERNAME_&$SMTP_USERNAME&" \
    -e "s&_SMTP_PASSWORD_&$SMTP_PASSWORD&" \
    -e "s&_FROM_EMAIL_&$FROM_EMAIL&" \
    -e "s&_IMAP_SERVER_&$IMAP_SERVER&" \
    -e "s&_IMAP_PORT_&$IMAP_PORT&" \
    -i $HOME/.cache/envTiledViz

echo "==== Build Docker images ===="
echo "===== build connection Docker ====="
TVConnections/build_connect

echo "===== build Flask Docker ====="
TVWeb/FlaskDocker/build_flaskdock



echo "===== build HPC images : ====="
echo "====== Init : move postgresql dir ======"
#mv TVDatabase/postgresql ${HOME}/tmp/postgresql_$DATE
#ssh-keygen -t dsa -N '' -f ~/.ssh/id_dsa

echo "====== Magiea connection client ======"
# Copy HPC machine id in HPC running containers !
# Security breach.
# You must modify this key if it not the same server.
#cp -p ~/.ssh/id_rsa* TVConnections/mageianvidia/ssh

#docker build -t mageianvidia:latest  -f TVConnections/mageianvidia/Dockerfile .
TVConnections/build_mageia_latest
TVConnections/build_mageia8

# echo "====== Magiea 6 ======"
# docker build -t mageianvidia:6 -f TVConnections/mageianvidia/Dockerfile6 .

echo "====== Ubuntu connection client ======"
docker build -t tileubuntu -f TVConnections/tileubuntu/Dockerfile .


echo "====== End build dockers ======"
#mv ${HOME}/tmp/postgresql_$DATE TVDatabase/postgresql

if [[ $firewallT == y ]]; then
    echo "====== Activate FirewallT ======"
    # Capabilites pour executer python sans sudo (setcap -r pour l'enlever)
    echo "Set capabilites on python"
    sudo setcap cap_net_admin=eip $(realpath $(which python))
fi

echo "==== Start PostgreSQL ===="
./start_postgres

# TODO : git clone Countdown 360:
#cd TVWeb/apps/static/dist/js
#git clone https://github.com/johnschult/jquery.countdown360.git
