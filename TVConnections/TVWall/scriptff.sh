#!/bin/bash

DEBUG=false
INCOGNITO='-private'

TIMEWAIT=0

DATE=$(mydate)
APPLINK="$1"
echo "APPLINK='$APPLINK'"

# Scale on TiledViz views
APPSCALE=$2

# DISPLAYWIDTH=1920
# DISPLAYHEIGHT=2160
DISPLAYWIDTH=$(bc <<< 1920/$APPSCALE)
DISPLAYHEIGHT=$(bc <<< 2160/$APPSCALE)

WALLWIDTH=$((DISPLAYWIDTH*4))
WALLHEIGHT=$((DISPLAYHEIGHT*2))

APPWIDTH=$WALLWIDTH
APPHEIGHT=$WALLHEIGHT

HOSTFILE=./listhost

OUT=./launch_file.sh


while IFS='' read -r -u3 line2; do
    IFS=' ' read -r -a aline <<<${line2}
    echo ${aline[0]} ${aline[1]} ${aline[2]} ${aline[3]}
    host=${aline[0]}
    MYDISP=${aline[1]}

    SHIFTLEFT=$((DISPLAYWIDTH*${aline[2]}))
    SHIFTTOP=$((DISPLAYHEIGHT*${aline[3]}))
    OUTLOG="/tmp/out_firefox_${MYDISP}_${DATE}.log"

    RET=$?
    if  [ $RET -eq 0 ]; then
	APPSRC=$(echo ${APPLINK} | sed -e "s/\(.*\)/\1.{DISPLAYWIDTH=${DISPLAYWIDTH},DISPLAYHEIGHT=${DISPLAYHEIGHT},WALLWIDTH=${WALLWIDTH},WALLHEIGHT=${WALLHEIGHT},APPWIDTH=${APPWIDTH},APPHEIGHT=${APPHEIGHT},SHIFTLEFT=${SHIFTLEFT},SHIFTTOP=${SHIFTTOP},APPSCALE=${APPSCALE}}/")
    else
	APPSRC=${APPLINK}
    fi
    echo ${APPSRC}

    # First use 
    CreateProfile=$( ssh ${host} 'if [ -d '${HOME}'/.mozilla/firefox/*temp-profile-$(hostname)'${MYDISP}' ]; then echo false; else echo true; fi')
    echo "CreateProfile = $CreateProfile"
    if ( $CreateProfile ); then
	ssh ${host} 'DISPLAY=:'${MYDISP}' firefox -CreateProfile temp-profile-$(hostname)'${MYDISP}
    fi

    # COMMAND='ls ${HOME}/.mozilla/firefox/*temp-profile-$(hostname)${MYDISP} > ${HOME}/.mozilla/firefox/$(hostname)${MYDISP}'
    # ssh ${host} "MYDISP=$MYDISP $COMMAND"
    # if ($DEBUG); then
    # 	FIREFOXCOMMAND='firefox -profile $( cat ${HOME}/.mozilla/firefox/$(hostname)${MYDISP} ) --no-remote -purgecaches '${INCOGNITO}' --display :'${MYDISP}' file:///tmp/launch_'${MYDISP}_${DATE}'.html'
    # 	#-profile $(find ~/.mozilla/firefox -type d -name "*temp-profile-$(hostname)${MYDISP}")
    # 	# --allow-file-access-from-files --new-instance --start-fullscreen
    # else
    # 	FIREFOXCOMMAND='firefox -profile $( cat ${HOME}/.mozilla/firefox/$(hostname)${MYDISP} ) --no-remote -purgecaches '${INCOGNITO}' --display :'${MYDISP}' file:///tmp/launch_'${MYDISP}_${DATE}'.html'
    # 	# --allow-file-access-from-files --new-instance --start-fullscreen
    # 	# --disable-application-cache --aggressive-cache-discard --enable-aggressive-domstorage-flushing
    # fi
    ssh ${host} "DISPLAY=:${MYDISP} echo ${FIREFOXCOMMAND} > ${OUTLOG}"
    #    ssh ${host} "sed -e 's/WALLWIDTH/${WALLWIDTH}/g' -e 's/WALLHEIGHT/${WALLHEIGHT}/g' -e 's/APPWIDTH/${APPWIDTH}/g' -e 's/APPHEIGHT/${APPHEIGHT}/g' -e 's/SHIFTLEFT/${SHIFTLEFT}/' -e 's/SHIFTTOP/${SHIFTTOP}/' -e 's/APPSCALE/${APPSCALE}/' -e 's@APPSRC@${APPSRC}@' ~mmancip/VIZMDLS/WALL/launch.html > /tmp/launch_${MYDISP}_${DATE}.html; DISPLAY=:${MYDISP} MYDISP=${MYDISP} ${FIREFOXCOMMAND} >> ${OUTLOG} 2>&1 &" &
    #sudo npm install --global http-server@13.1.0
    ssh ${host} "OUT_http=/tmp/out_http-server_$(date +%F_%H-%M); which http-server > \${OUT_http} ; http-server -a localhost -c-1 --no-dotfiles --proxy http://localhost:8080 /tmp |grep -v 'favicon' >> \${OUT_http} 2>&1 &"
    echo "sed -e 's/WALLWIDTH/${WALLWIDTH}/g' -e 's/WALLHEIGHT/${WALLHEIGHT}/g' -e 's/APPWIDTH/${APPWIDTH}/g' -e 's/APPHEIGHT/${APPHEIGHT}/g' -e 's/SHIFTLEFT/${SHIFTLEFT}/' -e 's/SHIFTTOP/${SHIFTTOP}/' -e 's/APPSCALE/${APPSCALE}/' -e 's@APPSRC@${APPSRC}@' ~mmancip/VIZMDLS/WALL/launch.html > /tmp/launch_${MYDISP}_${DATE}.html; DISPLAY=:${MYDISP} firefox -profile \${HOME}/.mozilla/firefox/*.temp-profile-\$(hostname)${MYDISP} --no-remote -purgecaches ${INCOGNITO} --display :${MYDISP} http://localhost:8080/launch_${MYDISP}_${DATE}.html >> ${OUTLOG} 2>&1 &" | ssh ${host} -T "cat > /tmp/call_launchff"

    ssh ${host} "chmod u+x /tmp/call_launchff"
    ssh ${host} "/tmp/call_launchff"
    sleep $TIMEWAIT

    i=$(( i + 1 ))
done 3<${HOSTFILE}

while IFS='' read -r -u3 line2; do
    IFS=' ' read -r -a aline <<<${line2}
    host=${aline[0]}
    MYDISP=${aline[1]}
    ssh ${host} "DISPLAY=:${MYDISP} $PWD/replace"
done 3<${HOSTFILE}

sleep 1
while IFS='' read -r -u3 line2; do
    IFS=' ' read -r -a aline <<<${line2}
    echo ${aline[0]} ${aline[1]} ${aline[2]} ${aline[3]}
    host=${aline[0]}
    MYDISP=${aline[1]}
    OUTLOG="/tmp/out_firefox_${MYDISP}_${DATE}.log"
    
    ssh ${host} "pgrep -fa Firefox >> ${OUTLOG}"
    ssh ${host} "export DISPLAY=:${MYDISP}; wmctrl -l -G >> ${OUTLOG}"
    ssh ${host} "export DISPLAY=:${MYDISP}; wmctrl -l -G |grep Firefox | sed -e 's@\(0x[0-9a-f]*\) .*@\1@' >> ${OUTLOG}"
    ssh ${host} 'export DISPLAY=:'${MYDISP}'; wmctrl -i -r $( wmctrl -l -G |grep Firefox | sed -e "s&\(0x[0-9a-f]*\) .*&\1&" ) -b toggle,fullscreen >> '${OUTLOG}
done 3<${HOSTFILE}

sleep 4
if ($DEBUG); then
    clush -g visu 'ls -la /tmp/*'${DATE}'*'
else 
    clush -g visu 'rm /tmp/*'${DATE}'*'
fi
