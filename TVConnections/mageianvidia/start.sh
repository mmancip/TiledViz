#!/bin/sh

RESOL=3840x2160

ARGS=$@
#echo ${ARGS[@]}

#1920x1080
myUID=1000
myGID=1000
myPORT=55555
myFront=localhost
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

# Change ldconfig paths if no nvidia device
if [ ! -e /dev/nvidia0 ]; then
	rm -f /etc/ld.so.conf.d/GL.conf
	ldconfig
fi

echo "start X "
export DISPLAY=:1

# Create the xstartup file
echo "#!/bin/bash 
source ~/.bashrc
export DISPLAY=$DISPLAY
sleep 1
xterm -rv -geometry ${RESOL}-0-0 -e /opt/client_python ${DOCKERID} ${myPORT} ${myFront} &

sleep 1
icewm-light
xterm
#unset SESSION_MANAGER
#unset DBUS_SESSION_BUS_ADDRESS
" >${HOME_user}/.vnc/xstartup
chmod 755 ${HOME_user}/.vnc/xstartup

chown -R myuser:myuser ${HOME_user}

echo export DOCKERID=$DOCKERID >> ${HOME_user}/.bashrc


cd
echo $( hostname )

echo "#!/bin/bash 
export LD_LIBRARY_PATH=/lib64:/usr/lib64/nvidia-current:/usr/lib64:/usr/lib64/dri
#TODO tested : export LD_LIBRARY_PATH=/lib64:/usr/lib64/nvidia-current:/usr/lib64:/usr/lib64/dri
Xvfb ${DISPLAY} -screen 0 ${RESOL}x24 2>&1 |tee -a $LOGFILE &
sleep 2
${HOME_user}/.vnc/xstartup
" >${HOME_user}/startx
chown myuser:myuser ${HOME_user}/startx
chmod a+x ${HOME_user}/startx

chown -R myuser:myuser ${HOME_user}

# Start and wait for either Xvfb to be fully up or we hit the timeout.
su - myuser -l -c ${HOME_user}/startx
#ls -al /root/.vnc/
#exec xterm 
