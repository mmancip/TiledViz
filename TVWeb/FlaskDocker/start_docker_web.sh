#!/bin/bash

/etc/init.d/ssh start


export POSTGRES_HOST=$1
export POSTGRES_DB=$2
export POSTGRES_USER=$3
export POSTGRES_PASSWORD="$4"
export flaskhost=$5
export UserId=$6
export GroupId=$7
shift 7
export SECRET_KEY="$@"

groupadd -r -g $UserId flaskusr && useradd -r -u $GroupId -g flaskusr flaskusr && \
    cp -rp /etc/skel /home/flaskusr && chown -R flaskusr:flaskusr /home/flaskusr

# addgroup --gid $7 flaskusr
# adduser --system --uid $6 --gid $7 --disabled-password flaskusr
#su - ssh-keygen -b 1024 -t rsa -N '' -f /home/flaskusr/.ssh/id_rsa

# patch codegen if needed :
cd /flask_venv/lib/python3.*/site-packages/sqlacodegen;
/TiledViz/TVDatabase/patch_flask_sqlacodegen /TiledViz

# patch flask-bootstrap for Radioform in quick_form macro
sed -e 's&    {% for item in field -%}&      <p class="label-block">{{field.label|safe}}</p>\n      <p class="help-block">{{field.description|safe}}</p>\n    {% for item in field -%}&' -i /flask_venv/lib/python3.*/site-packages/flask_bootstrap/templates/bootstrap/wtf.html

# ln -s /TiledViz/TVWeb/FlaskDocker/noVNC /etc/nginx/sites-available/noVNC
# ln -s /etc/nginx/sites-available/noVNC /etc/nginx/sites-enabled/
ln -s /TiledViz/TVWeb/noVNC /var/www/html/
#sed -e 's&error_log /var/log/nginx/error.log;&error_log /var/log/nginx/error.log debug;&' -i /etc/nginx/nginx.conf
# Prevent nginx error at startup if IPV6 is disabled on master host
sed -e 's&listen \[\:\:\]\:80 default_server;&#listen [::]:80 default_server;&' -i /etc/nginx/sites-available/default
nginx -g "daemon off;" &

if ($debug_Flask); then
    su - flaskusr -c '/bin/bash -vx -c /TiledViz/TVWeb/FlaskDocker/launch_flask ' $POSTGRES_HOST $POSTGRES_DB $POSTGRES_USER "$POSTGRES_PASSWORD" $flaskhost "$SECRET_KEY"
else
    su - flaskusr /TiledViz/TVWeb/FlaskDocker/launch_flask $POSTGRES_HOST $POSTGRES_DB $POSTGRES_USER "$POSTGRES_PASSWORD" $flaskhost "$SECRET_KEY"
fi
