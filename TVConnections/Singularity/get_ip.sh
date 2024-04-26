#!/bin/bash
ENO=$1
ip -4 -o addr show $ENO | awk '{print $4}' | cut -d "/" -f 1 > $HOME/.vnc/myip
