# Docker file mageianvidia
FROM mageia:5 
MAINTAINER  "Martial Mancip" <Martial.Mancip@MaisondelaSimulation.fr>

RUN urpmi --force lib64mesagl1-10.5.9-3.mga5.x86_64 xkbcomp-1.2.4-6.mga5 x11-data-xkbdata x11-font-alias tigervnc-server-1.3.1-6.mga5 \
                  openssh xauth-1.0.9-3.mga5  xterm xset htop mesa-demos x11vnc xrandr \
		  lib64sane1 lib64gtk+3_0 lib64virtualgl virtualgl wget htop man socat \
		  lib64lapack3
RUN urpmi --replacepkgs cracklib-dicts
RUN cd / \
   && rpm2cpio http://ftp.snt.utwente.nl/pub/os/linux/mageia/distrib/5/x86_64/media/nonfree/updates/x11-driver-video-nvidia-current-384.111-1.mga5.nonfree.x86_64.rpm |cpio -i -d 
#http://distrib-coffee.ipsl.jussieu.fr/pub/linux/Mageia/distrib/5/x86_64/media/nonfree/updates/x11-driver-video-nvidia-current-352.79-3.mga5.nonfree.x86_64.rpm |cpio -i -d 

RUN urpmi --force \
	 fluid-soundfont-gm-3.1-11.mga5 \
	 fonts-dejavu-common-2.34-4.mga5 \
	 fonts-ttf-bitstream-vera-1.10-15.mga5 \
	 fonts-ttf-decoratives-1.4-5.mga5 \
	 fonts-ttf-dejavu-2.34-4.mga5 \
	 fonts-ttf-liberation-2.00.1-4.mga5 \
	 fonts-ttf-west_european-1.4-5.mga5 \
	 ghostscript-fonts-8.11-19.mga5 \
	 gnu-free-fonts-compat-20120503-7.mga5 \
	 gnu-free-mono-fonts-20120503-7.mga5 \
	 gnu-free-sans-fonts-20120503-7.mga5 \
	 gnu-free-serif-fonts-20120503-7.mga5 \
         gnu-free-fonts-common-20120503-7.mga5 \
	 x11-font-adobe-75dpi-1.0.3-5.mga5 \
	 x11-font-bh-75dpi-1.0.3-5.mga5 \
	 x11-font-bh-lucidatypewriter-75dpi-1.0.3-5.mga5 \
	 x11-font-bitstream-75dpi-1.0.3-5.mga5 \
	 x11-font-bitstream-type1-1.0.3-5.mga5 \
	 x11-font-cursor-misc-1.0.3-5.mga5 \
	 x11-font-misc-misc-1.1.2-5.mga5 \
	 x11-font-type1-1.0.0-12.mga5 \
	 x11-font-xfree86-type1-1.0.4-5.mga5 \
	 xorg-x11-75dpi-fonts-7.7-6.mga5 \
        && /bin/dbus-uuidgen --ensure

RUN urpmi --force alsa-utils lib64fribidi0 xdg-utils wmctrl xprop xwininfo openssh-clients xwd netpbm\
   && cd / \
   && rpm2cpio http://ftp.snt.utwente.nl/pub/os/linux/mageia/distrib/5/x86_64/media/core/release/icewm-light-1.3.7-14.mga5.x86_64.rpm |cpio -i -d \
   && rpm2cpio http://ftp.snt.utwente.nl/pub/os/linux/mageia/distrib/5/x86_64/media/core/release/icewm-i18n-1.3.7-14.mga5.noarch.rpm |cpio -i -d 
#http://distrib-coffee.ipsl.jussieu.fr/pub/linux/Mageia/distrib/5/x86_64/media/

RUN urpmi --force ntp && sed -e "s/1.pool.ntp*/time.extra.cea.fr iburst/" -e "s/server [23].pool.ntp.*//" -i /etc/ntp.conf && ln -s /usr/share/zoneinfo/Europe/Paris /etc/localtime


RUN urpmi python

ENTRYPOINT ["/start.sh"]

COPY ssh /home/myuser/.ssh/

COPY vnccommand /opt/vnccommand
COPY tunnel_ssh /opt/tunnel_ssh

RUN touch /home/myuser/.Xauthority

COPY .bashrc /home/myuser/.bashrc

COPY nvlinks /root/nvlinks

COPY movewindows /opt/movewindows

COPY client_python /opt/client_python
COPY TileClient.py /opt/TileClient.py

COPY start.sh /start.sh
CMD ["-r","800x600","-u","1000","-g","1000","-p","55555","-h","localhost"]


