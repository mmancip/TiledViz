# .bashrc

if [ -e /dev/nvidia0 ]; then
    LD_LIBRARY_PATH=/usr/local/lib64:/lib64:/usr/lib64:/usr/lib64/dri:/usr/lib64/nvidia390
    PATH=/usr/lib64/nvidia390/bin:/usr/local/sbin:/usr/sbin:/usr/local/bin:/usr/bin
else
    LD_LIBRARY_PATH=/usr/local/lib64:/usr/lib64
    PATH=/usr/local/sbin:/usr/sbin:/usr/local/bin:/usr/bin
fi

ENV=$HOME/.bashrc
USERNAME="myuser"
export USERNAME ENV PATH LD_LIBRARY_PATH

# Source global definitions
if [ -f /etc/bashrc ]; then
	. /etc/bashrc
fi
