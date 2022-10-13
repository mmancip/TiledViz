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
patch -p0 < ../patch_ui
cd ..
cp vnc_multi.html noVNC
cp ui_multi.js noVNC/app
cp rfb_multi.js noVNC/core
#patch -p0 < patch_devices_noVNC 
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
