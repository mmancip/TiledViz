#!/bin/bash

# Test Docker rights
docker ps -a

# Build Virtualenv for TVSecure
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
patch -p0 < ../patch_ui
cd ..
cp vnc_multi.html noVNC
cp ui_multi.js noVNC/app
cp rfb_multi.js noVNC/core
#patch -p0 < patch_devices_noVNC 
popd

echo "==== Get noVNC ===="
pushd TVConnections
git clone https://github.com/novnc/websockify
popd

# Launch postgresql docker
echo "==== Launch postgresql docker ===="
if ( $installX11 ); then
    password=$(python3 -c "import zenipy; password=zenipy.zenipy.password(title='PostgreSQL password',text='Please give a password for your postgresql DB : (no '@' or '/' !)', width=450, height=120, timeout=None); print(str(password))")
else
    echo "Please give a password for your postgresql DB : (no '@' or '/' !)"
    read -s password;
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
    SMTP=$(python3 -c "import zenipy; myserver=zenipy.zenipy.password(title='SMTP server address',text='Please give your SMTP server address - the outgoing mail server.', width=450, height=120, timeout=None); print(str(myserver))")
    NTP=$(python3 -c "import zenipy; myserver=zenipy.zenipy.password(title='NTP server address',text='Please give your NTP server address - the time server.', width=450, height=120, timeout=None); print(str(myserver))")
else
    echo "Please give the PUBLIC SSL key PATH."
    read SSLpublic;
    echo "Please give the PRIVATE SSL key PATH."
    read SSLprivate;

    echo "Please give your SMTP server address - the outgoing mail server."
    read SMTP;
    echo "Please give your NTP server address - the time server."
    read NTP;
fi

sed -e "s&DNSservername&$SERVER_NAME&"  -e "s&_DOMAIN_&$DOMAIN&" -e "s&_SSLpublic_&$SSLpublic&" -e "s&_SSLprivate_&$SSLprivate&" -e "s&_NTP_&$NTP&"  -e "s&_SMTP_&$SMTP&" -i $HOME/.cache/envTiledViz

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
