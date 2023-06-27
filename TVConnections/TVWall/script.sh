#!/bin/bash 

DEBUG=false
INCOGNITO='--incognito --no-first-run'
#--ignore-certificate-errors 
# no default browser option ??????

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
    OUTLOG="/tmp/out_chrome_${MYDISP}_${DATE}.log"

    RET=$?
    if  [ $RET -eq 0 ]; then
	APPSRC=$(echo ${APPLINK} | sed -e "s/\(.*\)/\1.{DISPLAYWIDTH=${DISPLAYWIDTH},DISPLAYHEIGHT=${DISPLAYHEIGHT},WALLWIDTH=${WALLWIDTH},WALLHEIGHT=${WALLHEIGHT},APPWIDTH=${APPWIDTH},APPHEIGHT=${APPHEIGHT},SHIFTLEFT=${SHIFTLEFT},SHIFTTOP=${SHIFTTOP},APPSCALE=${APPSCALE}}/")
    else
	APPSRC=${APPLINK}
    fi
    echo ${APPSRC}

    if ($DEBUG); then
	CHROMECOMMAND="google-chrome ${INCOGNITO} --user-data-dir=/tmp/temp-profile-${MYDISP} --new-window --display=:${MYDISP} --start-fullscreen file:///tmp/launch_${MYDISP}_${DATE}.html"
    else
	CHROMECOMMAND="google-chrome ${INCOGNITO} --user-data-dir=/tmp/temp-profile-${MYDISP} --new-window --display=:${MYDISP} --start-fullscreen --disable-application-cache --aggressive-cache-discard --enable-aggressive-domstorage-flushing file:///tmp/launch_${MYDISP}_${DATE}.html"
    fi
    ssh ${host} "echo ${CHROMECOMMAND} > ${OUTLOG}"
    ssh ${host} "sed -e 's/WALLWIDTH/${WALLWIDTH}/g' -e 's/WALLHEIGHT/${WALLHEIGHT}/g' -e 's/APPWIDTH/${APPWIDTH}/g' -e 's/APPHEIGHT/${APPHEIGHT}/g' -e 's/SHIFTLEFT/${SHIFTLEFT}/' -e 's/SHIFTTOP/${SHIFTTOP}/' -e 's/APPSCALE/${APPSCALE}/' -e 's@APPSRC@${APPSRC}@' ~mmancip/VIZMDLS/WALL/launch.html > /tmp/launch_${MYDISP}_${DATE}.html; DISPLAY=:${MYDISP}  ${CHROMECOMMAND} >> ${OUTLOG} 2>&1 &" &

    sleep $TIMEWAIT

    i=$(( i + 1 ))
done 3<${HOSTFILE}


sleep 4
if ($DEBUG); then
    clush -g visu 'ls -la /tmp/*'${DATE}'*'
else 
    clush -g visu 'rm /tmp/*'${DATE}'*'
fi
