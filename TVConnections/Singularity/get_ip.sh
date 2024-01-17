ip -4 -o addr show eno1 | awk '{print $4}' | cut -d "/" -f 1 > .vnc/myip
