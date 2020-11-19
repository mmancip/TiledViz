# .bashrc

if [ -e /dev/nvidia0 ]; then
    LD_LIBRARY_PATH=/usr/lib/nvidia-current:/usr/lib/dri:$LD_LIBRARY_PATH
    PATH=/usr/lib/nvidia-current/bin:$PATH
fi

ENV=$HOME/.bashrc
USERNAME="myuser"
export USERNAME ENV PATH LD_LIBRARY_PATH

# Source global definitions
if [ -f /etc/bashrc ]; then
	. /etc/bashrc
fi
