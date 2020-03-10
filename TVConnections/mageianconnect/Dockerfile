# Docker file mageianvidia
FROM mageia:6
MAINTAINER  "Martial Mancip" <Martial.Mancip@MaisondelaSimulation.fr>

RUN dnf install -y lib64mesagl1 xkbcomp x11-data-xkbdata x11-font-alias tigervnc-server \
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
	 gnu-free-fonts-compat-20120503-8.mga6 \
	 gnu-free-mono-fonts-20120503-8.mga6 \
	 gnu-free-sans-fonts-20120503-8.mga6 \
	 gnu-free-serif-fonts-20120503-8.mga6 \
         gnu-free-fonts-common-20120503-8.mga6 \
	 x11-font-adobe-75dpi \
	 x11-font-bh-75dpi \
	 x11-font-bh-lucidatypewriter-75dpi \
	 x11-font-bitstream-75dpi \
	 x11-font-bitstream-type1 \
	 x11-font-type1 \
	 x11-font-xfree86-type1 \
	 xorg-x11-75dpi-fonts \
        && /bin/dbus-uuidgen --ensure

RUN dnf install -y alsa-utils lib64fribidi0 xdg-utils wmctrl openssh-clients xwd netpbm
RUN dnf --downloadonly --downloaddir=/tmp/cache install -y icewm-theme-oxygen-aya \
    && ls -la /tmp/cache \
    && rpm -ip /tmp/cache/icewm-theme-oxygen-aya*.rpm --nodeps \
    && dnf install -y icewm-light icewm-i18n --setopt=install_weak_deps=False --exclude=bootsplash,kernel-desktop

RUN dnf install -y python3-psycopg2 git rsync

COPY ./ /TiledViz

RUN pip3 install -r /TiledViz/TVConnections/requirements.txt ;


RUN cd /TiledViz/TVConnections/mageianconnect/ ; \
    mkdir -p /home/myuser ;\
    cp -rp ssh /home/myuser/.ssh/ ;\
    cp vnccommand /opt/vnccommand ;\
    cp .bashrc /home/myuser/.bashrc ;\
    cp switch_* /opt/ ;\
    cp start.sh /start.sh
    

ENTRYPOINT ["/start.sh"]

RUN touch /home/myuser/.Xauthority


CMD ["-1", "localhost", "TiledViz", "tiledviz", "m_test/@03", "-r","800x600","-u","1000","-g","1000"]


