#!/bin/bash

RESOL=3840x2160

ARGS=$@
#echo ${ARGS[@]}

#1920x1080
myUID=1000
myGID=1000
myPORT=55555
myFront=myuser@localhost
if [ -z "$1" ]; then
	echo Usage: $0 [-r RESOL_XxRESOL_Y] -u UID [-g GID] -p PORTserver -h Frontend
	exit 1
else
    IFS=' ' read -ra ADDR <<< "$ARGS"
    lenADDR=${#ADDR[@]}
    if [ ${lenADDR} -gt 0 ]; then
	i=0
	while [ $i -lt ${lenADDR} ]; do
	    case "${ADDR[$i]}" in
		'-r') 
		    RESOL=${ADDR[$((i+1))]};;
		'-u')
		    myUID=${ADDR[$((i+1))]};;
		'-g')
		    myGID=${ADDR[$((i+1))]};;
		'-p')
		    myPORT=${ADDR[$((i+1))]};;
		'-h')
		    myFront=${ADDR[$((i+1))]};;
		'.*')
		    myGID=${myUID}
	    esac
	    i=$((i+2));
	done
fi
fi


groupadd -g ${myGID} myuser
useradd -r -u ${myUID} -g myuser myuser
#adduser --disabled-password --gecos "My User" --uid 1000 myuser

HOME_user=/home/myuser
if [ -d ${HOME_user} ]; then
    mkdir -p ${HOME_user}/.vnc
fi 
chmod 700 ${HOME_user}/.vnc
chown -R myuser:myuser ${HOME_user}

chmod 600 ${HOME_user}/.ssh/config

LOGFILE=${HOME_user}/.vnc/$(hostname).log
touch $LOGFILE
chown myuser:myuser $LOGFILE

echo "start.sh with args : ${ARGS[*]}" >> $LOGFILE

if ! [ -e ${HOME_user}/.vnc/passwd ]; then
	if [ -z "$VNC_PASSWORD" ]; then
		choose() { echo -n ${1:$((RANDOM%${#1})):1}; }
		password=$({
			for i in $(seq 1 8); do
			    choose "-._+0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
			done
		})
		echo Random Password Generated: $password |tee -a $LOGFILE
		echo "$password" |xargs -I@ x11vnc -storepasswd @ ${HOME_user}/.vnc/passwd
	else
		echo "$VNC_PASSWORD" |xargs -I@ x11vnc -storepasswd @ ${HOME_user}/.vnc/passwd
	fi
	chmod 600 ${HOME_user}/.vnc/passwd

	sleep 1
else
    echo Random Password Generated: $(x11vnc -showrfbauth ${HOME_user}/.vnc/passwd |tail -1 |sed -e 's/.*pass: //' ) |tee -a $LOGFILE
fi
chown -R myuser:myuser ${HOME_user} 

echo "start X "

xvfbLockFilePath="/tmp/.X1-lock"
if [ -f "${xvfbLockFilePath}" ]
then
    log_i "Removing xvfb lock file '${xvfbLockFilePath}'..."
    if ! rm -v "${xvfbLockFilePath}"
    then
        log_e "Failed to remove xvfb lock file"
        exit 1
    fi
fi

echo "export HOSTNAME="${HOSTNAME} >> /etc/profile.d/env_variable.sh

# Set defaults if the user did not specify envs.
export DISPLAY=:1
#${XVFB_DISPLAY:-:1}
screen=${XVFB_SCREEN:-0}
resolution=${XVFB_RESOLUTION:-1280x960x24}
timeout=${XVFB_TIMEOUT:-5}

# Create the xstartup file
echo "#!/bin/sh 

sleep 1
xterm -rv -geometry ${RESOL}-0-0 -e /opt/client_python ${DOCKERID} ${myPORT} ${myFront} &

sleep 1
icewm
xterm
#unset SESSION_MANAGER
#unset DBUS_SESSION_BUS_ADDRESS
" >${HOME_user}/xstartup
chmod 755 ${HOME_user}/xstartup

chown -R myuser:myuser ${HOME_user}

echo export DOCKERID=$DOCKERID >> ${HOME_user}/.bashrc


# Run the vncserver
cd
echo $( hostname )
su - myuser -c " Xvfb ${DISPLAY} -screen ${screen} ${resolution} &"
loopCount=0
until xdpyinfo -display ${DISPLAY} > /dev/null 2>&1
do
    loopCount=$((loopCount+1))
    sleep 1
    if [ ${loopCount} -gt ${timeout} ]
    then
        log_e "xvfb failed to start"
        exit 1
    fi
done
su - myuser -c "${HOME_user}/xstartup "
#xinit -- :0"
su - myuser -c "x11vnc -forever -rfbport 5902 -noncache -cursor arrow -shared -nowf -display  ${DISPLAY} -rfbauth /home/myuser/.vnc/passwd -http > /tmp/out_x11vnc_$(date +%F_%H-%M) 2>&1"
