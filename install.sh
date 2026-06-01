#!/bin/bash

UseLastEnv=$1

echo "#==== Tiledviz installation script. ==="
echo "If you want to use graphical installation, you need to install zenity package on your system,"
echo "and set installX11=true in envTiledViz on your TiledViz source root, OK ?"
#read OK

source ./envTiledViz

# if asked installX11 in ./envTiledViz rerun with graphical progress bar.
if ( $instalX11 ) & [ X"$GraphicalInstall" != Xtrue ]; then
    export GraphicalInstall=true
    echo "Restart with graphical progression bar."
    sleep 3
    ( ./install.sh $UseLastEnv ) | zenity --progress --title="Progress Status" --text="First Task" --percentage=0 --auto-kill
    #--auto-close
    exit 0
fi

echo "1"

echo "# Test Docker rights"
echo $(docker ps -a)
echo "5"

# Build Virtualenv for TVSecure
# if UseLastEnv is null, build a new environement
if [ X"$UseLastEnv" == X"" ]; then
    echo "#==== Build new Virtualenv for TVSecure ===="
    export DATE=$(date +%F_%H-%M-%S)
    echo "#DATE=$DATE"

    mkdir TiledVizEnv_${DATE}
    python3 -m venv TiledVizEnv_${DATE}
    source TiledVizEnv_${DATE}/bin/activate
    echo "8"
    
    echo "#==== Copy TiledViz env in .cache ===="
    [ ! -d $HOME/.cache ] && mkdir $HOME/.cache
    sed -e "s&DATE=.*&DATE=$DATE&" envTiledViz > $HOME/.cache/envTiledViz
    chmod 600 $HOME/.cache/envTiledViz
    echo "9"
    
    ls -la $HOME/.cache/envTiledViz
    source $HOME/.cache/envTiledViz
    echo "# Build Env OK."

else
    echo "#==== Retreive old configuration ===="
    OLDENV=$(find . -maxdepth 1 -type d -name "TiledVizEnv_*" |tail -1)
    export DATE_ENV=$(echo $OLDENV |sed -e 's&\./TiledVizEnv_&&')
    source $OLDENV/bin/activate
    echo "8"
    
    ls -la $HOME/.cache/envTiledViz
    source $HOME/.cache/envTiledViz
    if [ ${DATE_ENV} != ${DATE} ]; then
	echo "#Error restart install : DATEs not equal ${DATE_ENV} != ${DATE}."
	sleep 10
	exit 1
    fi
    echo "# Retrieve Env OK."
fi

echo "10"

echo "#===== Enable FirewallT Tiledviz ====="

if ( $installX11 ); then
    zenity  --question --title "TiledViz firewall" --text " Activate firewallT for Tiledviz ?"
    elsefirewallT=$?
    [[ $firewallT == 0 ]] && firewallT=y || firewallT=n
else
    echo "Activate firewallT for Tiledviz ? : ('n' or 'y')"
    read -s firewallT;
    [[ $firewallT == y || $firewallT == n ]] && echo "Valid Input" || echo "Invalid Input"
fi

echo "#==== Install environment ===="
TiledVizEnv_$DATE/bin/python3 -m pip install --upgrade pip
# TiledViz packages
pip3 install -r requirements.txt

echo "20"

# Get noVNC
echo "#==== Get noVNC ===="
pushd TVWeb
git clone https://github.com/novnc/noVNC.git noVNC
echo "25"
cd noVNC
git checkout v1.7.0
patch -p0 < ../patch_ui
cd ..
cp vnc_multi.html noVNC
cp ui_multi.js noVNC/app
cp rfb_multi.js noVNC/core
#patch -p0 < patch_devices_noVNC
popd
echo "27"

echo "#==== Get websockify ===="
pushd TVConnections
git clone https://github.com/novnc/websockify
popd

echo "30"

# Launch postgresql docker
echo "#==== Prepare postgresql docker ===="
if ( $installX11 ); then
    Outz=$(zenity  --width=600 --forms --title="Postgres DB" \
		   --text="Create Postgres Docker."\
		   --add-entry="Docker name (default: ${postgresNAME})" --add-entry="External PORT (default: ${POSTGRES_PORT})" --add-password="Password (forbiden '@', '&', '/', '|')")
    $(echo $Outz | sed -e 's&\([^|]*\)|\([^|]*\)|\([^|]*\)&export POSTG_NAME="\1"  export POSTG_PORT="\2" export password="\3"&')
else
    echo "Please give the Docker name of PostGresQL DB (default: ${postgresNAME})."
    read POSTG_NAME;
    echo "Please give its external PORT (default: ${POSTGRES_PORT})."
    read POSTG_PORT;

    echo "Please give a password for your postgresql DB : (forbiden '@', '/', '|' !)"
    read -s password
fi
[ X"$POSTG_NAME" == X ] && export POSTG_NAME=$postgresNAME
[ X"$SSLprivate" == X ] && export POSTG_PORT=$POSTGRES_PORT
replpass=$( echo $password | sed -e "s|\&|\\\&|g" -e 's|"||g' )

sed -e "s&${postgresNAME}&$POSTG_NAME&" \
    -e "s&${POSTGRES_PORT}&$POSTG_PORT&" \
    -e "s|your_postgres_password|$replpass|" \
    -i $HOME/.cache/envTiledViz
echo "32"

echo "#==== Copy tiledViz.conf in $HOME/.tiledviz cache dir ===="
mkdir $HOME/.tiledviz
cp tiledviz.conf $HOME/.tiledviz
[[ $firewallT == y ]] && sed -e "s|FirewallT=False|FirewallT=True|" -i $HOME/.tiledviz/tiledviz.conf 
echo "33"

echo "#=== Web Server URL ==="
if ( $installX11 ); then
    webserver=$(zenity --forms --title="Web server informations" --text="SSL web server.domain name" --add-entry="Server name" --add-entry="Domain extension" )
    $(echo $webserver |sed -e 's&\([^|]*\)|\([^|]*\)&export SERVER_NAME="\1" export DOMAIN="\2"&')
else
    echo "Please give a SERVER.DOMAIN for your SSL web server"
    read myweb;
    IFS='.' read -r -a webline <<<$myweb

    # Array slice
    serv="${webline[@]: 0:$((${#webline[*]}-2))}"
    SERVER_NAME=$(echo $serv |sed -e "s/ /./g")
    DOMAIN=${webline[${#webline[*]}-2]}.${webline[${#webline[*]}-1]}
fi

echo "35"


if ( $installX11 ); then
    Outz=$(zenity  --width=600 --forms --title="Web connections informations" \
		   --text="SSL, SMTP, MAIL ( outgoing mail server for 2FA )."\
		   --add-entry="SSL PUBLIC key path" --add-entry="SSL PRIVATE key path" --add-entry="TiledViz email.")
    $(echo $Outz | sed -e 's&\([^|]*\)|\([^|]*\)|\([^|]*\)&export SSLpublic="\1"  export SSLprivate="\2" export FROM_EMAIL="\3"&')

    Outz=$(zenity  --width=600 --forms --title="SMTP server for some TiledSet cases"  \
		   --add-entry="SMTP server address (optionnal)" \
		   --add-entry="SMTP server PORT" \
		   --add-entry="SMTP server username" \
		   --add-password="SMTP server password" )
    $(echo $Outz | sed -e 's&\([^|]*\)|\([^|]*\)|\([^|]*\)|\([^|]*\)&export SMTP_SERVER="\1" export SMTP_PORT="\2" export SMTP_USERNAME="\3" export SMTP_PASSWORD="\4"&')
   
    Outz=$(zenity  --question --title "SMTP server" --text "SSL option ?" )
    SMTP_USE_SSL=$( [[ $? == 0 ]] && echo true || echo false )
    Outz=$(zenity  --question --title "SMTP server" --text "TLS option ?" )
    SMTP_USE_TLS=$( [[ $? == 0 ]] && echo true || echo false )

    Outz=$(zenity  --width=600 --forms --title="IMAP and NTP (optionnal)" \
		   --text="IMAP server ( the ingoing mail server ) | NTP server ( time server )" \
		   --add-entry="IMAP server address" \
		   --add-entry="IMAP server PORT " \
		   --add-entry="NTP server address" )
    $(echo $Outz | sed -e 's&\([^|]*\)|\([^|]*\)|\([^|]*\)&export IMAP_SERVER="\1" export IMAP_PORT="\2" export NTP="\3"&')

    echo "#$SSLpublic $SSLprivate $SMTP_SERVER $SMTP_PORT $SMTP_USE_SSL $SMTP_USE_TLS $SMTP_USERNAME $SMTP_PASSWORD $FROM_EMAIL $IMAP_SERVER $IMAP_PORT $NTP"
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
SMTP_PASSWORD=$( echo $SMTP_PASSWORD | sed -e "s|\&|\\\&|g" -e 's|"||g' )

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

echo "40"

# ==========================================================
echo "==== Start PostgreSQL ===="
./start_postgres
echo "50"

sleep 2

echo "#==== Build Docker images ===="
echo "#===== build connection Docker ====="
TVConnections/build_connect

echo "60"

echo "#===== build Flask Docker ====="
TVWeb/FlaskDocker/build_flaskdock

echo "70"

echo "#===== build HPC images : ====="
echo "#====== Magiea connection client ======"

TVConnections/build_mageia_latest
TVConnections/build_mageia8

echo "80"

echo "#====== Ubuntu connection client ======"
docker build -t tileubuntu -f TVConnections/tileubuntu/Dockerfile .

echo "90"

echo "#====== End build dockers ======"
#mv ${HOME}/tmp/postgresql_$DATE TVDatabase/postgresql

if [[ $firewallT == y ]]; then
    echo "#====== Activate FirewallT ======"
    # Capabilites pour executer python sans sudo (setcap -r pour l'enlever)
    echo "Set capabilites on python"
    sudo setcap cap_net_admin=eip $(realpath $(which python))
fi
echo "100"

# TODO : git clone Countdown 360:
#cd TVWeb/apps/static/dist/js
#git clone https://github.com/johnschult/jquery.countdown360.git


echo "# All finished."
