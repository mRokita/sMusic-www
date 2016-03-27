# -*- coding: utf-8 -*-
from flask import request, render_template, redirect, current_app, session, url_for
from werkzeug.routing import RequestRedirect
import flask
from flask_login import login_required, current_user, UserMixin, \
    fresh_login_required, login_fresh
from passlib.apps import custom_app_context as pwd_context

from forms import LoginForm
from shared import app, db
from utils import get_or_create, secure_random_string_generator, Singleton
from access_control import User, control_controllers_perm, vote_perm
import json
import config


class VotePoint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    amount = db.Column(db.Integer)
    expire_date = db.DateTime(timezone=True)


class Track(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    points = db.Column(db.Integer)


@app.route('/api/v1/controllers/voting_system/vote_for/<artist_id>/<album_id>/<track_id>/<points>/')
@vote_perm.require(http_exception=403)
def vote_for(artist_id, album_id, track_id, points):
    if get_total_point() < points:
        return json.dumps({"request": "error", "type": "not_enough_points"})
    pass


def get_total_point():
    pass


def check_points_regen():
    last_regen = json.loads(Singleton.query.filter_by(name="vote_system_last_check").first())


def update_queue():
    pass


@app.route('/api/v1/controllers/voting_system/start')
@control_controllers_perm.require(http_exception=403)
def start():
    pass


@app.route('/api/v1/controllers/voting_system/stop')
@control_controllers_perm.require(http_exception=403)
def stop():
    pass
