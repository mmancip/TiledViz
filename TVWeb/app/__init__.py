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
logging.basicConfig(level=logging.WARNING)
rootLogger = logging.getLogger()
rootLogger.setLevel(logging.WARNING)
fileHandler = logging.FileHandler("TiledViz.log")
fileHandler.setLevel(logging.WARNING)
fileHandler.setFormatter(logFormatter)
rootLogger.addHandler(fileHandler)
outHandler = logging.StreamHandler(sys.stdout)
outHandler.setLevel(logging.WARNING)
# outHandler.setLevel(logging.DEBUG)
outHandler.setFormatter(logFormatter)
rootLogger.addHandler(outHandler)

logging.getLogger('root').setLevel(logging.WARNING)
logging.getLogger('socketio').setLevel(logging.ERROR)
logging.getLogger('engineio').setLevel(logging.ERROR)
# logging.getLogger("urllib3").setLevel(logging.WARNING)
# logging.getLogger('requests').setLevel(logging.CRITICAL)
logging.getLogger('werkzeug').setLevel(logging.ERROR)


app = Flask(__name__)
app.config.from_object(Config) # There are given the secret key and other app settings
bootstrap = Bootstrap(app)
socketio = SocketIO(app) # Replaces app.run()
#socketio = io.connect({transports: ['websocket']});
#,ping_interval=100000
#cors_allowed_origins ? List of origins that are allowed to connect to this server. All origins are allowed by default.

db = SQLAlchemy(app)
logging.info("Flask-SocketIO server for TiledViz up and running")

from app import routes
