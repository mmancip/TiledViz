/sbin/ip -4 -o addr show eth0 | awk '{print $4}' | cut -d "/" -f 1 > .vnc/myip
