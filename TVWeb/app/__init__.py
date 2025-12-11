#! python3
# -*- coding: utf-8 -*-

from gevent import monkey
monkey.patch_all()

from flask import Flask
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap5
from flask_wtf.csrf import CSRFProtect
                    
from gevent.pywsgi import WSGIServer

import os

from config import Config
#from app import config


# Logging configuration # TODO: maybe switch to a config file ?
import logging, sys
logFormatter = logging.Formatter("%(asctime)s - %(threadName)s - %(levelname)s: %(message)s ")
logging.basicConfig(level=logging.WARNING)
rootLogger = logging.getLogger()
rootLogger.setLevel(logging.WARNING)
fileHandler = logging.FileHandler("TiledViz.log")
# Attention : TiledViz Log file is watching by TVSecure (hôte?) process
#             If you change logging level to DEBUG this super process may not work correctly.
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


#SQLALCHEMY_DATABASE_URI=os.environ("DATABASE_URL")
app = Flask(__name__)
app.config.from_object(Config) # There are given the secret key and other app settings

logging.debug("Flask App config for TiledViz : "+str(app.config))

bootstrap = Bootstrap5(app)

#import ssl
#ssl.PROTOCOL_SSLv23 = ssl.PROTOCOL_TLSv1

async_mode = "gevent"
socketio = SocketIO(app,async_mode=async_mode,ssl_context=(os.getenv('SSLpublic'),os.getenv('SSLprivate')))
#socketio = io.connect({transports: ['websocket']});
#,ping_interval=100000
#cors_allowed_origins ? List of origins that are allowed to connect to this server. All origins are allowed by default.
csrf = CSRFProtect(app)

db = SQLAlchemy(app)

# Initialize Flask-Mail
from app.email_utils import init_mail
mail = init_mail(app)

logging.warning("Flask-SocketIO server for TiledViz up and running")

from app import routes
