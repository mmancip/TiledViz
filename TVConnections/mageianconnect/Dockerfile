# Docker file mageiaconnect
FROM mageia:7
MAINTAINER  "Martial Mancip" <Martial.Mancip@MaisondelaSimulation.fr>

ENV SMTP TODO_SMTP

RUN dnf install -y lib64mesagl1 xkbcomp x11-server-xvfb x11-data-xkbdata x11-font-alias \
                  openssh xauth  xterm xset htop mesa-demos x11vnc xrandr \
		  lib64sane1 lib64gtk+3_0 lib64virtualgl virtualgl wget htop man socat \
		  lib64lapack3
    
#RUN urpmi --replacepkgs cracklib-dicts
RUN dnf install -y  dnf-plugins-core \
    && dnf config-manager --add-repo /etc/yum.repos.d/mageia-nonfree-x86_64.repo \
    && dnf config-manager --set-enabled mageia-x86_64-nonfree updates-x86_64-nonfree \
    && dnf install -y x11-driver-video-nvidia-current --setopt=install_weak_deps=False 

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
	 
RUN dnf install -y alsa-utils lib64fribidi0 xdg-utils wmctrl openssh-clients xwd netpbm gettext
RUN dnf --downloadonly --downloaddir=/tmp/cache install -y icewm-theme-oxygen-aya \
    && ls -la /tmp/cache \
    && rpm -ip /tmp/cache/icewm-theme-oxygen-aya*.rpm --nodeps \
    && dnf install -y icewm-light icewm-i18n --setopt=install_weak_deps=False --exclude=bootsplash,kernel-desktop

RUN dnf install -y python3-psycopg2 git rsync python3-pip ipython && \
    pip3 install --upgrade pip wheel numpy

RUN dnf install -y ntp \
    && sed -e "s/1.pool.ntp*/time.extra.cea.fr iburst/" -e "s/server [23].pool.ntp.*//" -i /etc/ntp.conf \
    && rm /etc/localtime \
    && ln -s /usr/share/zoneinfo/Europe/Paris /etc/localtime

RUN dnf install -y postfix \
    && echo "relayhost=$SMTP"  >> /etc/postfix/main.cf \
    && sed -e "s&inet_protocols = all&inet_protocols = ipv4&" -i /etc/postfix/main.cf

COPY ./ /TiledViz

RUN rm -rf /TiledViz/TVFiles/* /TiledViz/launch_TiledViz

RUN pip3 install -r /TiledViz/TVConnections/requirements.txt ;

RUN cd /TiledViz/TVConnections/mageianconnect/ && \
    mkdir -p /home/myuser &&\
    cp -rp ssh /home/myuser/.ssh/ &&\
    cp vnccommand /opt/vnccommand &&\
    cp .bashrc /home/myuser/.bashrc &&\
    cp switch_* /opt/ &&\
    cp /etc/inputrc /home/myuser/.inputrc &&\
    cp start.sh /start.sh
    
COPY TVConnections/cat_between /

RUN mkdir /home/myuser/.tiledviz
COPY tiledviz.conf /home/myuser/.tiledviz

ENTRYPOINT ["/start.sh"]

RUN touch /home/myuser/.Xauthority


CMD ["-1", "localhost", "6431", "TiledViz", "tiledviz", "m_test/@03", "-r","800x600","-u","1000","-g","1000","-d"]


