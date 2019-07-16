#!/bin/bash

/etc/init.d/ssh start

groupadd -r -g $7 flaskusr && useradd -r -u $6 -g flaskusr flaskusr && \
    cp -rp /etc/skel /home/flaskusr && chown -R flaskusr:flaskusr /home/flaskusr

# addgroup --gid $7 flaskusr
# adduser --system --uid $6 --gid $7 --disabled-password flaskusr
#su - ssh-keygen -b 1024 -t rsa -N '' -f /home/flaskusr/.ssh/id_rsa

# patch flask-bootstrap for Radioform in quick_form macro
sed -e 's&    {% for item in field -%}&      <p class="label-block">{{field.label|safe}}</p>\n      <p class="help-block">{{field.description|safe}}</p>\n    {% for item in field -%}&' -i /flask_venv/lib/python3.7/site-packages/flask_bootstrap/templates/bootstrap/wtf.html

# ln -s /TiledViz/TVWeb/FlaskDocker/noVNC /etc/nginx/sites-available/noVNC
# ln -s /etc/nginx/sites-available/noVNC /etc/nginx/sites-enabled/
ln -s /TiledViz/TVWeb/noVNC /var/www/html/
#sed -e 's&error_log /var/log/nginx/error.log;&error_log /var/log/nginx/error.log debug;&' -i /etc/nginx/nginx.conf
nginx -g "daemon off;" &

#apt-get install -y apache2
#cp -rp /TiledViz/TVWeb/noVNC/ /var/www/html/noVNC
#vi /etc/apache2/sites-available/000-default.conf 
#/etc/init.d/apache2 restart

su - flaskusr /TiledViz/TVWeb/FlaskDocker/launch_flask $1 $2 $3 $4 $5

