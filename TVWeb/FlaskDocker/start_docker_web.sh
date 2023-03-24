#!/bin/bash

/etc/init.d/ssh start


export POSTGRES_HOST=$1
export POSTGRES_PORT=$2
export POSTGRES_DB=$3
export POSTGRES_USER=$4
export POSTGRES_PASSWORD="$5"
export flaskhost=$6
export UserId=$7
export GroupId=$8
shift 8
export SECRET_KEY="$@"

groupadd -r -g $GroupId flaskusr && useradd -r -u $UserId -g flaskusr flaskusr && \
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
#sed -e 's&listen \[\:\:\]\:80 default_server;&#listen [::]:80 default_server;&' -i /etc/nginx/sites-available/default
rm /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default
cp -f /TiledViz/TVWeb/nginx/nginx.conf /etc/nginx/
sed -e "s&DNSservername&$SERVER_NAME.$DOMAIN&"  -e "s&/DOMAIN/&/$DOMAIN/&" -e "s&_SSLpublic_&$SSLpublic&" -e "s&_SSLprivate_&$SSLprivate&" -i /etc/nginx/nginx.conf
chown root:root  /etc/nginx/nginx.conf
echo nginx -g "daemon off;"
nginx -g "daemon off;" &

if ($debug_Flask); then
    su flaskusr -w DOMAIN,SERVER_NAME,SSLpublic,SSLprivate -c "/bin/bash -vx -c \"cd /TiledViz/TVWeb; FlaskDocker/launch_flask $POSTGRES_HOST $POSTGRES_PORT $POSTGRES_DB $POSTGRES_USER '$POSTGRES_PASSWORD' $flaskhost '$SECRET_KEY'\""
    while true; do sleep 10; done
else
    su - flaskusr -w DOMAIN,SERVER_NAME,SSLpublic,SSLprivate -c "/bin/bash -c \"cd /TiledViz/TVWeb; FlaskDocker/launch_flask $POSTGRES_HOST $POSTGRES_PORT $POSTGRES_DB $POSTGRES_USER '$POSTGRES_PASSWORD' $flaskhost '$SECRET_KEY'\""
fi
