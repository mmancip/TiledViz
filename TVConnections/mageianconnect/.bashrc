# .bashrc

if [ -e /dev/nvidia0 ]; then
    LD_LIBRARY_PATH=/usr/lib64:/usr/lib64/nvidia-current:/usr/lib64/dri
    PATH=/usr/lib64/nvidia-current/bin:/usr/local/sbin:/usr/sbin:/usr/local/bin:/usr/bin
else
    PATH=/usr/local/sbin:/usr/sbin:/usr/local/bin:/usr/bin
fi

ENV=$HOME/.bashrc
USERNAME="myuser"
export USERNAME ENV PATH LD_LIBRARY_PATH

# Source global definitions
if [ -f /etc/bashrc ]; then
	. /etc/bashrc
fi
