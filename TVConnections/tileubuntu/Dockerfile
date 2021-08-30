FROM ubuntu:18.04

RUN cat /etc/resolv.conf  && echo "nameserver 8.8.8.8" >> /etc/resolv.conf \
 && echo "nameserver 8.8.4.4" >> /etc/resolv.conf && echo 1 && cat /etc/resolv.conf

RUN apt-get update && \
    apt-get install -y --fix-missing xvfb xterm xinit wmctrl icewm \
	python3-psycopg2 git rsync python3-pip iproute2 && \
    pip3 install --upgrade pip wheel 

RUN ln -s /usr/bin/python3 /usr/bin/python

# RUN apt-get install -y ntp \
#     && sed -e "s/1.pool.ntp*/time.extra.cea.fr iburst/" -e "s/server [23].pool.ntp.*//" -i /etc/ntp.conf \
#     && rm /etc/localtime \
#     && ln -s /usr/share/zoneinfo/Europe/Paris /etc/localtime

RUN sed -i -e 's&# deb-src &deb-src &' /etc/apt/sources.list && \
    apt-get update && \
    apt-get build-dep -y --fix-missing x11vnc

RUN cd /usr/src && git clone https://github.com/LibVNC/x11vnc.git && \
    cd x11vnc && autoreconf -fiv && ./configure && make install

RUN apt-get autoclean \
    && apt-get clean

COPY TVConnections/mageianvidia/ssh /home/myuser/.ssh/

COPY TVConnections/tileubuntu/.bashrc /home/myuser/.bashrc
COPY TVConnections/mageianvidia/tunnel_ssh /opt/tunnel_ssh
COPY TVConnections/tileubuntu/start.sh /start.sh

ENTRYPOINT ["/start.sh"]

RUN touch /home/myuser/.Xauthority

COPY TVConnections/tileubuntu/client_python /opt/client_python
COPY TVConnections/tileubuntu/TileClient.py /opt/TileClient.py

COPY TVConnections/connect /usr/lib/python3/dist-packages/connect

COPY TVConnections/get_ip.sh /usr/local/bin

RUN mkdir /home/myuser/.tiledviz
COPY tiledviz.conf /home/myuser/.tiledviz

CMD ["-r","800x600","-u","1000","-g","1000","-p","55555","-h","localhost"]
