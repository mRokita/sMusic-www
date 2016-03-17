#-*- coding: utf-8 -*-
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
global app
global db

try:
    app
except NameError:
    global app
    app = Flask(__name__)
    global db
    db = SQLAlchemy(app)
