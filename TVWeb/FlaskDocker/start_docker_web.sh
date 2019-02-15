#!/bin/bash

groupadd -r -g 1002 flaskusr && useradd -r -u 1002 -g flaskusr flaskusr && \
    cp -rp /etc/skel /home/flaskusr && chown -R flaskusr:flaskusr /home/flaskusr

# patch flask-bootstrap for Radioform in quick_form macro
sed -e 's&    {% for item in field -%}&      <p class="label-block">{{field.label|safe}}</p>\n      <p class="help-block">{{field.description|safe}}</p>\n    {% for item in field -%}&' -i /flask_venv/lib/python3.5/site-packages/flask_bootstrap/templates/bootstrap/wtf.html

su - flaskusr /TiledViz/TVWeb/FlaskDocker/launch_flask $1 $2 $3 $4 $5

