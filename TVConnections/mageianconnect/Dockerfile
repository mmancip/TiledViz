# Docker file mageiaconnect
FROM mageia:8
MAINTAINER  "Martial Mancip" <Martial.Mancip@MaisondelaSimulation.fr>

RUN dnf install -y lib64mesagl1 xkbcomp x11-server-xvfb xdpyinfo xinit x11-data-xkbdata x11-font-alias \
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
	 gnu-free-fonts-compat \
	 gnu-free-mono-fonts \
	 gnu-free-sans-fonts \
	 gnu-free-serif-fonts \
         gnu-free-fonts-common \
	 x11-font-adobe-75dpi \
	 x11-font-bh-75dpi \
	 x11-font-bh-lucidatypewriter-75dpi \
	 x11-font-bitstream-75dpi \
	 x11-font-bitstream-type1 \
	 x11-font-type1 \
	 x11-font-xfree86-type1 \
	 xorg-x11-75dpi-fonts \
        && /bin/dbus-uuidgen --ensure

RUN dnf install -y alsa-utils lib64fribidi0 xdg-utils wmctrl openssh-server openssh-clients xwd netpbm gettext
RUN dnf --downloadonly --downloaddir=/tmp/cache install -y icewm-theme-oxygen-aya \
    && ls -la /tmp/cache \
    && rpm -ip /tmp/cache/icewm-theme-oxygen-aya*.rpm --nodeps \
    && dnf install -y icewm-light icewm-i18n --setopt=install_weak_deps=False --exclude=bootsplash,kernel-desktop

RUN dnf install -y python3-psycopg2 git rsync python3-pip ipython && \
    pip3 install --upgrade wheel numpy

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
    
COPY TVConnections/mageianconnect/sshd_config /etc/ssh
RUN chown root:root /etc/ssh/sshd_config

COPY TVConnections/cat_between /

RUN mkdir /home/myuser/.tiledviz
COPY tiledviz.conf /home/myuser/.tiledviz

ENTRYPOINT ["/start.sh"]

RUN touch /home/myuser/.Xauthority


CMD ["-1", "localhost", "6431", "TiledViz", "tiledviz", "m_test/@03", "-r","800x600","-u","1000","-g","1000","-p","22222","-d"]

RUN bash -c "echo 'LD_LIBRARTY_PATH=/usr/local/lib64:$LD_LIBRARY_PATH' >> /etc/profile; sed -e 's&nvidia390&nvidia-current&' -i /home/myuser/.bashrc" 

# TODO
ENV SMTPserver TODO_SMTP
ENV NTPserver TODO_NTP
 
RUN dnf install -y postfix \
    && echo "relayhost=$SMTPserver"  >> /etc/postfix/main.cf \
    && sed -e "s&inet_protocols = all&inet_protocols = ipv4&" -i /etc/postfix/main.cf

RUN dnf install -y ntp \
    && sed -e "s/1.pool.ntp*/$NTPserver iburst/" -e "s/server [23].pool.ntp.*//" -i /etc/ntp.conf \
    && rm -f /etc/localtime \
    && ln -s /usr/share/zoneinfo/Europe/Paris /etc/localtime
