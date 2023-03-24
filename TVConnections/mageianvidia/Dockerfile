# Docker file mageianvidia
FROM mageia:7
MAINTAINER  "Martial Mancip" <Martial.Mancip@MaisondelaSimulation.fr>

RUN dnf install -y lib64mesagl1 xkbcomp x11-data-xkbdata x11-font-alias tigervnc-server \
                  openssh xauth  xterm xset htop mesa-demos x11vnc xrandr \
		  lib64sane1 lib64gtk+3_0 lib64virtualgl virtualgl wget htop man socat \
		  lib64lapack3
    
#RUN urpmi --replacepkgs cracklib-dicts
RUN dnf install -y  dnf-plugins-core \
    && dnf config-manager --add-repo /etc/yum.repos.d/mageia-nonfree-x86_64.repo \
    && dnf config-manager --set-enabled mageia-x86_64-nonfree updates-x86_64-nonfree \
    && dnf install -y x11-driver-video-nvidia390 --setopt=install_weak_deps=False 

RUN dnf install -y  \
	 fluid-soundfont-gm \
	 fonts-dejavu-common \
	 fonts-ttf-bitstream-vera \
	 fonts-ttf-decoratives \
	 fonts-ttf-dejavu \
	 fonts-ttf-liberation \
	 fonts-ttf-west_european \
	 ghostscript-fonts \
	 x11-font-adobe-75dpi \
	 x11-font-bh-75dpi \
	 x11-font-bh-lucidatypewriter-75dpi \
	 x11-font-bitstream-75dpi \
	 x11-font-bitstream-type1 \
	 x11-font-type1 \
	 x11-font-xfree86-type1 \
	 xorg-x11-75dpi-fonts \
        && /bin/dbus-uuidgen --ensure

RUN urpmi  -y  \
	 gnu-free-fonts-compat-20120503-9 \
	 gnu-free-mono-fonts-20120503-9 \
	 gnu-free-sans-fonts-20120503-9 \
	 gnu-free-serif-fonts-20120503-9 \
         gnu-free-fonts-common-20120503-9
	 
RUN dnf install -y alsa-utils lib64fribidi0 xdg-utils wmctrl xdotool openssh-clients xwd netpbm
RUN dnf --downloadonly --downloaddir=/tmp/cache install -y icewm-theme-oxygen-aya \
    && ls -la /tmp/cache \
    && rpm -ip /tmp/cache/icewm-theme-oxygen-aya*.rpm --nodeps \
    && dnf install -y icewm-light icewm-i18n --setopt=install_weak_deps=False --exclude=bootsplash,kernel-desktop

RUN dnf install -y git rsync python3-pip && \
    pip3 install --upgrade pip

RUN dnf install -y ntp \
    && sed -e "s/1.pool.ntp*/time.extra.cea.fr iburst/" -e "s/server [23].pool.ntp.*//" -i /etc/ntp.conf \
    && rm /etc/localtime \
    && ln -s /usr/share/zoneinfo/Europe/Paris /etc/localtime

RUN dnf install -y python python-pip \
    && pip2 install wheel numpy pexpect configparser

COPY TVConnections/mageianvidia/ssh /home/myuser/.ssh/

COPY TVConnections/mageianvidia/vnccommand /opt/vnccommand
COPY TVConnections/mageianvidia/.bashrc /home/myuser/.bashrc
COPY TVConnections/mageianvidia/tunnel_ssh /opt/tunnel_ssh
COPY TVConnections/mageianvidia/start.sh /start.sh

ENTRYPOINT ["/start.sh"]

RUN touch /home/myuser/.Xauthority

COPY TVConnections/mageianvidia/movewindows /opt/movewindows

COPY TVConnections/mageianvidia/client_python /opt/client_python
COPY TVConnections/TileClient.py /opt/TileClient.py

COPY TVConnections/connect /usr/lib64/python2.7/site-packages/connect

COPY TVConnections/get_ip.sh /usr/local/bin

RUN mkdir /home/myuser/.tiledviz
COPY tiledviz.conf /home/myuser/.tiledviz

CMD ["-r","800x600","-u","1000","-g","1000","-p","55555","-h","localhost"]


