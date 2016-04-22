# -*- coding: utf-8 -*-
from flask import request, render_template, redirect, current_app, session, url_for
from werkzeug.routing import RequestRedirect
import flask
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin, \
    fresh_login_required, login_fresh
from flask_principal import Principal, Identity, AnonymousIdentity, identity_changed, identity_loaded, RoleNeed, \
    UserNeed, Permission, TypeNeed
from flask_admin import Admin, AdminIndexView
import flask_admin
from flask_admin.contrib import sqla
from passlib.apps import custom_app_context as pwd_context

from shared import app, db
from utils import get_or_create, secure_random_string_generator
import access_control
import config
import json


class Radio(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    access_key = db.Column(db.String(32), unique=True)
    comment = db.Column(db.String(1024))
    column_display_pk = False
    users = db.relationship("User", back_populates="radio")

    def generate_new_access_key(self):
        self.access_key = secure_random_string_generator(32)

    def __init__(self, name="none", access_key=""):
        self.name = name
        if access_key=="":
            self.generate_new_access_key()
        else:
            self.access_key = access_key

    def __str__(self):
        return "%s - %s" % (self.id, self.name)


class RadioAdmin(sqla.ModelView):
    form_columns = ['name', 'comment']
    column_exclude_list = ['access_key']
    form_excluded_columns = ('password',)
    column_searchable_list = ('name',)


