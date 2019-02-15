#! python3
# -*- coding: utf-8 -*-

from flask import Flask
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from config import Config

# Logging configuration # TODO: maybe switch to a config file ?
import logging, sys
logFormatter = logging.Formatter("%(asctime)s - %(threadName)s - %(levelname)s: %(message)s ")
rootLogger = logging.getLogger()
rootLogger.setLevel(logging.DEBUG)
fileHandler = logging.FileHandler("TiledViz.log")
fileHandler.setLevel(logging.DEBUG)
fileHandler.setFormatter(logFormatter)
rootLogger.addHandler(fileHandler)
outHandler = logging.StreamHandler(sys.stdout)
outHandler.setLevel(logging.DEBUG)
outHandler.setFormatter(logFormatter)
rootLogger.addHandler(outHandler)


app = Flask(__name__)
app.config.from_object(Config) # There are given the secret key and other app settings
bootstrap = Bootstrap(app)
socketio = SocketIO(app) # Replaces app.run()
#,ping_interval=100000
#cors_allowed_origins ? List of origins that are allowed to connect to this server. All origins are allowed by default.

logging.getLogger('socketio').setLevel(logging.ERROR)
logging.getLogger('engineio').setLevel(logging.ERROR)

db = SQLAlchemy(app)
logging.info("Flask-SocketIO server for TiledViz up and running")

from app import routes
