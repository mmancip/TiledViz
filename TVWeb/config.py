# -*- coding: utf-8 -*-

import os

class Config(object):
    SECRET_KEY = os.environ.get("SECRET_KEY") or "I-am-a-funny-unicorn" # Syntax to enable locally defined (fine-tuned) variables, or default, more generic ones
    SQLALCHEMY_DATABASE_URI = "postgresql://"+os.getenv('POSTGRES_USER')+":"+os.getenv('POSTGRES_PASSWORD')+"@"+os.getenv('POSTGRES_HOST')+":"+os.getenv('POSTGRES_PORT')+"/"+os.getenv('POSTGRES_DB') # TODO: avoid credentials + right adress
    SQLALCHEMY_TRACK_MODIFICATIONS = True # Avoid warnings
