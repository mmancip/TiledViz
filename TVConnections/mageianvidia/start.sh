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
		echo "$password" | vncpasswd -f >${HOME_user}/.vnc/passwd
	else
		echo "$VNC_PASSWORD" | vncpasswd -f >${HOME_user}/.vnc/passwd
	fi
	chmod 600 ${HOME_user}/.vnc/passwd

	sleep 1
fi
chown -R myuser:myuser ${HOME_user} 

echo "start X "

# Create the xstartup file
echo "#!/bin/sh 

xterm -rv -geometry ${RESOL}-0-0 -e /opt/client_python ${DOCKERID} ${myPORT} ${myFront} &
icewm-light
#unset SESSION_MANAGER
#unset DBUS_SESSION_BUS_ADDRESS
" >${HOME_user}/.vnc/xstartup
chmod 755 ${HOME_user}/.vnc/xstartup

chown -R myuser:myuser ${HOME_user}

echo export DOCKERID=$DOCKERID >> ${HOME_user}/.bashrc


# Run the vncserver
cd
echo $( hostname )
su - myuser -c "/usr/bin/vncserver -geometry ${RESOL}  -fg  2>&1 |tee -a $LOGFILE"
#exec /usr/bin/Xvnc -geometry ${RESOL}   
#:1 -geometry 1024x768 -fp catalogue:/etc/X11/fontpath.d -autokill  -rfbwait 30000 -rfbauth /root/.vnc/passwd -rfbport 5901 -pn
#ls -al /root/.vnc/
#exec xterm 
