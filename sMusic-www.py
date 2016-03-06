#-*- coding: utf-8 -*-
from __future__ import print_function
from functools import wraps
import flask
from flask import request, Response, Flask, render_template, redirect, current_app, session, Markup
import radio_utils
from forms import *
import json
import sys
import config
import re
from urllib import urlopen, urlencode
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from flask.ext.principal import Principal, Identity, AnonymousIdentity, identity_changed, identity_loaded, RoleNeed,\
    UserNeed

app = Flask(__name__)

__version__ = "0.1.1 Alpha"
ALBUM_ART_URL = "http://www.slothradio.com/covers/?adv=0&artist={}&album={}"
PATTERN_ALBUM_ART = re.compile("\\<div class\\=\\\"album0\\\"\\>\\<img src\\=\\\"(.*?)\\\"")
PATTERN_FIX_ALBUM = re.compile("( ?\\(.*?\\))|(\\ ?[Dd][Ii][Ss][Cc] \d)|(\\ ?[Cc][Dd] \d)|(\\&)|(\\,)|( UK)|( US)")
CHAR_FIX = {u"ó": u"o",
            u"ź": u"z",
            u"ł": u"l",
            u"ą": u"a",
            u"ś": u"s",
            u"ć": u"c",
            u"ę": u"e",
            u"ń": u"n"}

app.config['SQLALCHEMY_DATABASE_URI'] = config.database_uri
app.secret_key = config.secret_key
db = SQLAlchemy(app)

roles_users = db.Table('roles_users',
        db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
        db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))


class Role(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)

    def __init__(self, name):
        self.name = name


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))

    def __init__(self, login, password, roles):
        self.login = login
        self.password = password
        self.active = True
        self.roles = roles

principals = Principal(app)
login_manager = LoginManager(app)
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    wrong_login = False

    if form.validate_on_submit():
        user = User.query.filter_by(login=form.login.data).first()

        if user is not None and form.password.data == user.password:
            login_user(user, remember=form.remember)
            identity_changed.send(current_app._get_current_object(),
                                  identity=Identity(user.id))
            flask.flash('Logged in successfully.')

            return form.redirect()
        else:
            wrong_login = True

    return render_template('login.html', form=form, wrong_login=wrong_login)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    for key in ('identity.name', 'identity.auth_type'):
        session.pop(key, None)

    identity_changed.send(current_app._get_current_object(),
                          identity=AnonymousIdentity())
    return redirect('/')


@identity_loaded.connect_via(app)
def on_identity_loaded(sender, identity):
    # Set the identity user object
    identity.user = current_user

    if hasattr(current_user, 'id'):
        identity.provides.add(UserNeed(current_user.id))

    if hasattr(current_user, 'roles'):
        for role in current_user.roles:
            identity.provides.add(RoleNeed(role.name))


@app.before_first_request
def create_default_user():
    db.create_all()
    adm_role = Role('admin')
    db.session.add(adm_role)
    admin = User(config.admin_login, config.admin_password, [adm_role])
    db.session.add(admin)
    db.session.commit()


def fix_chars(string):
    for char in CHAR_FIX:
        string = string.replace(char, CHAR_FIX[char])
    return string


def check_auth():
    """
    Ta funkcja sprawdza, czy dane logowania są prawidłowe
    """
    auth = request.authorization
    return auth and auth.username == config.admin_login and auth.password == config.admin_password


def render_template_with_args(template, **kwargs):
    return render_template(template, radio_utils=radio_utils, version=__version__, **kwargs)


@app.route('/')
def ui_player():
    return render_template_with_args("player.html", is_logged_in = check_auth())


@app.route('/library/')
@login_required
def ui_library():
    return render_template_with_args("library_artists.html")


@app.route('/search/')
@login_required
def ui_library_search():
    query = request.args["q"]
    return render_template_with_args("library_search.html", query=query)


@app.route('/library/<artist>/')
@login_required
def ui_library_artist(artist):
    return render_template_with_args("library_artist_albums.html", artist=artist)


@app.route('/library/<artist>/<album>/')
@login_required
def ui_library_artist_album(artist, album):
    return render_template_with_args("library_artist_album_tracks.html", artist=artist, album=album)


@app.route('/api/v1/library/')
@login_required
def api_v1_library():
    return json.dumps(radio_utils.get_artists())


@app.route('/api/v1/library/<artist>/')
@login_required
def api_v1_library_artist(artist):
    return json.dumps(radio_utils.get_albums(artist))


@app.route('/api/v1/library/<artist>/<album>/')
@login_required
def api_v1_library_artist_album(artist, album):
    return json.dumps(radio_utils.get_tracks(artist, album))


@app.route('/api/v1/play_next/')
@login_required
def api_v1_play_next():
    return json.dumps(radio_utils.play_next())


@app.route('/api/v1/play_prev/')
@login_required
def api_v1_play_prev():
    return json.dumps(radio_utils.play_prev())


@app.route('/api/v1/pause/')
@login_required
def api_v1_pause():
    return json.dumps(radio_utils.pause())


@app.route('/api/v1/vol/<value>/')
@login_required
def api_v1_vol(value):
    return json.dumps(radio_utils.set_vol(value))


@app.route('/api/v1/status/')
def api_v1_status():
    return json.dumps(radio_utils.get_status())


@app.route('/api/v1/clear_q_and_play/<artist_id>/<album_id>/<track_id>/')
@login_required
def api_v1_clear_q_and_play(artist_id, album_id, track_id):
    return json.dumps(radio_utils.clear_queue_and_play(artist_id, album_id, track_id))


@app.route('/api/v1/clear_queue/')
@login_required
def api_v1_clear_queue():
    return json.dumps(radio_utils.clear_queue())


@app.route('/api/v1/add_to_q/<artist_id>/<album_id>/<track_id>/')
@login_required
def api_v1_add_to_q(artist_id, album_id, track_id):
    return json.dumps(radio_utils.add_to_queue(artist_id, album_id, track_id))


@app.route('/api/v1/current_queue/')
def api_v1_current_queue():
    return json.dumps(radio_utils.get_current_queue())


@app.route('/api/v1/search_track/<query>')
@login_required
def api_v1_search_track(query):
    return json.dumps(radio_utils.search_for_track(query))


@app.route('/api/v1/albumart/<artist>/<album>/')
def api_v1_album_art(artist, album):
    url = ALBUM_ART_URL.format(unicode(fix_chars(artist).encode("utf-8")), PATTERN_FIX_ALBUM.sub("", unicode(fix_chars(album).encode("utf-8"))))
    return redirect(PATTERN_ALBUM_ART.findall(urlopen(url).read())[0], 302)


@app.route('/api/v1/play/')
@login_required
def play():
    return json.dumps(radio_utils.play())

if __name__ == '__main__':
    app.debug = True
    app.run(host="0.0.0.0")
