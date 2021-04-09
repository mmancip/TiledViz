#!/bin/sh

RESOL=3840x2160

# mail system
#postfix start

ARGS=$@
#echo ${ARGS[@]}

#1920x1080
myUID=1000
myGID=1000

export ConnectionId=$1
export POSTGRES_HOST=$2
export POSTGRES_DB=$3
export POSTGRES_USER=$4
export POSTGRES_PASSWORD="$5"

if [ -z "$5" ]; then
	echo Usage: $0 ConnectionId POSTGRES_HOST POSTGRES_DB POSTGRES_USER POSTGRES_PASSWORD [-r RESOL_XxRESOL_Y] -u UID [-g GID] [-d]
	exit 1
else
    IFS=' ' read -ra ADDR <<< "$ARGS"

    lenADDR=${#ADDR[@]}
    if [ ${lenADDR} -gt 0 ]; then
	i=5
	while [ $i -lt ${lenADDR} ]; do
	    case "${ADDR[$i]}" in
		'-r') 
		    RESOL=${ADDR[$((i+1))]};;
		'-u')
		    myUID=${ADDR[$((i+1))]};;
		'-g')
		    myGID=${ADDR[$((i+1))]};;
		'-d')
		    debug=true;;
		'.*')
		    myGID=${myUID}
	    esac
	    i=$((i+2));
	done
fi
fi


/etc/init.d/postfix start

groupadd -g ${myGID} myuser
useradd -r -u ${myUID} -g myuser myuser
HOME_user=/home/myuser
chmod 700 ${HOME_user}/.vnc
chown -R myuser:myuser ${HOME_user}

chmod 600 ${HOME_user}/.ssh/config

LOGFILE=${HOME_user}/.vnc/$(hostname).log
touch $LOGFILE
chown myuser:myuser $LOGFILE

echo "start.sh with args : ${ARGS[*]}" >> $LOGFILE

if ! [ -e ${HOME_user}/.vnc/passwd ]; then
    choose() { echo -n ${1:$((RANDOM%${#1})):1}; }
    password=$({
		  for i in $(seq 1 8); do
		      choose "-._+0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
		  done
	      })
    echo Random Password Generated: $password |tee -a $LOGFILE
    echo "$password" |xargs -I@ x11vnc -storepasswd @ ${HOME_user}/.vnc/passwd
    chmod 600 ${HOME_user}/.vnc/passwd

    sleep 1
else
    echo Random Password Generated: $(x11vnc -showrfbauth ${HOME_user}/.vnc/passwd |tail -1 |sed -e 's/.*pass: //' ) |tee -a $LOGFILE
fi
chown -R myuser:myuser ${HOME_user} 

# Change ldconfig paths if no nvidia device
if [ ! -e /dev/nvidia0 ]; then
	rm -f /etc/ld.so.conf.d/GL.conf
	ldconfig
fi

echo "start X "

export DISPLAY=:1

# Create the xstartup file
echo "#!/bin/bash
. /home/myuser/.bashrc
sleep 1
pgrep -fa Xvfb
export DISPLAY=$DISPLAY
icewm-light &

/opt/vnccommand &

sleep 1
if [ X\"$debug\" != X ]; then optDEB=1; fi
stty sane
export TERM=linux
xterm -rv -fullscreen -fa 'Adobe Courrier:size=12:antialias=true' -e /TiledViz/TVConnections/tvconnections.sh ${ConnectionId} ${POSTGRES_HOST} ${POSTGRES_DB} ${POSTGRES_USER} '${POSTGRES_PASSWORD}' \$optDEB
" >${HOME_user}/.vnc/xstartup
chmod 755 ${HOME_user}/.vnc/xstartup

chown -R myuser:myuser ${HOME_user}

echo export DOCKERID=$DOCKERID >> ${HOME_user}/.bashrc

# Build database model
sqlacodegen postgresql://${POSTGRES_USER}:"${POSTGRES_PASSWORD}"@${POSTGRES_HOST}/${POSTGRES_DB} --outfile=/TiledViz/TVDatabase/TVDb/models.py

# Run the vncserver
cd
echo $( hostname )


echo "#!/bin/bash
ssh-keygen -b 1024 -t rsa -N '' -f ~myuser/.ssh/id_rsa 
Xvfb ${DISPLAY} -screen 0 ${RESOL}x24 2>&1 |tee -a $LOGFILE &
sleep 2
${HOME_user}/.vnc/xstartup
" >${HOME_user}/startx
chown myuser:myuser ${HOME_user}/startx
chmod a+x ${HOME_user}/startx

cat ${HOME_user}/startx

su - myuser -l -c ${HOME_user}/startx
#ls -al /root/.vnc/
#exec xterm 
