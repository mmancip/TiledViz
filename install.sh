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

echo "==== Install environment ===="
pip3 install -r requirements.txt

# Get noVNC
echo "==== Get noVNC ===="
pushd TVWeb
git clone https://github.com/novnc/noVNC.git noVNC
cd noVNC
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

echo "==== Build Docker images ===="
echo "===== build connection Docker ====="
docker build -t mageiaconnect -f TVConnections/mageianconnect/Dockerfile .

echo "===== build HPC images : ====="
echo "====== Init : move postgresql dir ======"
#mv TVDatabase/postgresql ${HOME}/tmp/postgresql_$DATE
#ssh-keygen -t dsa -N '' -f ~/.ssh/id_dsa

echo "====== Magiea 7 ======"
# Copy HPC machine id in HPC running containers !
# Security breach.
# You must modify this key if it not the same server.
cp -p ~/.ssh/id_rsa* TVConnections/mageianvidia/ssh

docker build -t mageianvidia:7 -f TVConnections/mageianvidia/Dockerfile .
docker tag mageianvidia:7 mageianvidia:latest 

echo "====== Magiea 6 ======"
docker build -t mageianvidia:6 -f TVConnections/mageianvidia/Dockerfile6 .

echo "====== Ubuntu 18.04 ======"
docker build -t tileubuntu -f TVConnections/tileubuntu/Dockerfile .


echo "===== build Flask Docker ====="
docker build -t flaskimage -f TVWeb/FlaskDocker/Dockerfile.web .

echo "====== End build dockers ======"
#mv ${HOME}/tmp/postgresql_$DATE TVDatabase/postgresql


echo "==== Start PostgreSQL ===="
./start_postgres

echo "=== Add SSL certificates ==="
if ( $installX11 ); then
    myweb=$(python3 -c "import zenipy; myweb=zenipy.zenipy.password(title='SSL web server.domain name',text='Please give a SERVER.DOMAIN for your SSL web server.', width=450, height=120, timeout=None); print(str(myweb))")
else
    echo "Please give a SERVER.DOMAIN for your SSL web server"
    read -s myweb;
fi
IFS='.' read -r -a webline <<<$myweb

# Array slice
serv="${webline[@]: 0:$((${#webline[*]}-2))}"
SERVER_NAME=$(echo $serv |sed -e "s/ /./g")
DOMAIN=${webline[${#webline[*]}-2]}.${webline[${#webline[*]}-1]}

sed -e "s&_SERVER_NAME_&$SERVER_NAME&"  -e "s&_DOMAIN_&$DOMAIN&" -i TVWeb/FlaskDocker/Dockerfile.web
sed -e "s&DNSservername&$SERVER_NAME.$DOMAIN&"  -e "s&/DOMAIN/&/$DOMAIN/&" -i TVWeb/nginx/nginx.conf

sed -e "s&DNSservername&$SERVER_NAME&"  -e "s&_DOMAIN_&$DOMAIN&"  -i $HOME/.cache/envTiledViz

# TODO : letsencrypt SSL certificate validation and
#        usability for users in docker in
#        /etc/letsencrypt/archive//$DOMAIN/fullchain1.pem and privatekey1.pem (cf TVSecure.py)
# idée : on ouvre le répertoire en tant que root, on lance la commande et on referme le répertoire pour ne plus donner l'accès.
# idée 2 : vérifier l'intégritée de TiledViz pour les accès root avec un git diff et bloquer les lancements si il y a eu des modifs ?


# TODO : git clone Countdown 360:
#cd TVWeb/apps/static/dist/js
#git clone https://github.com/johnschult/jquery.countdown360.git
