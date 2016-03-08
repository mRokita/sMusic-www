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
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin,\
    fresh_login_required
from flask_principal import Principal, Identity, AnonymousIdentity, identity_changed, identity_loaded, RoleNeed,\
    UserNeed, Permission, PermissionDenied
from flask_admin import Admin, AdminIndexView
import flask_admin
from flask_admin.contrib import sqla
from passlib.apps import custom_app_context as pwd_context
import ldap3
import os
import logging

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

    def __str__(self):
        return "%s - %s" % (self.id, self.name)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    display_name = db.Column(db.String(255))
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))
    comment = db.Column(db.String(255))

    def __init__(self):
        pass

    def __init__(self, login="none", password="", roles=[]):
        self.login = login
        self.display_name = login
        self.password = pwd_context.encrypt(password)
        self.active = True
        self.roles = roles

    def __str__(self):
        return "%s - %s - %s" % (self.id, self.login, self.display_name)

principals = Principal(app)
admin_perm = Permission(RoleNeed("admin"))
music_control_perm = Permission(RoleNeed("dj"))
library_browse_perm = Permission(RoleNeed("ANY"))

@app.context_processor
def inject_is_admin():
    return dict(is_admin=admin_perm.can())

login_manager = LoginManager(app)
login_manager.init_app(app)
login_manager.login_view = "login"


class MyAdminIndexView(AdminIndexView):
    @flask_admin.expose('/')
    @admin_perm.require(http_exception=403)
    @fresh_login_required
    def index(self):
        return super(MyAdminIndexView, self).index()


admin = Admin(app, name='sMusic', index_view=MyAdminIndexView())


class UserAdmin(sqla.ModelView):
    form_columns = ['login', 'display_name', 'password', 'active', 'roles', 'comment']
    column_exclude_list = ['password']
    column_display_pk = False
    column_searchable_list = ('login', 'display_name')


class RoleAdmin(sqla.ModelView):
    can_create = False
    can_delete = False
    form_columns = ['users']

admin.add_view(UserAdmin(User, db.session))
admin.add_view(RoleAdmin(Role, db.session))


def check_ldap_credentials(login, password):
    try:
        conn = ldap3.Connection(ldap3.Server(config.ldap_host, use_ssl=True), "cn=%s, cn=Users, dc=ad, dc=staszic, dc=waw, dc=pl" % login, password,
                                auto_bind=True, raise_exceptions=False) #sprawdzic bezpieczenstwo polaczenia
        ret = conn.search("cn=Users, dc=ad, dc=staszic, dc=waw, dc=pl", "(cn=%s)" % login, attributes=['uidNumber', 'displayName'])
        if not ret:
            return False
        data = conn.entries
        if len(data) == 1:
            ldap_data = dict()
            ldap_data['login'] = login
            ldap_data['uid'] = int(data[0]['uidNumber'][0])
            ldap_data['class_id'] = int(int(str(data[0]['uidNumber'][0])[0:3]))
            ldap_data['display_name'] = str(data[0]['displayName'][0])
            return ldap_data
        else:
            return False
    except KeyError:
        return False
    except IndexError:
        return False
    except ldap3.LDAPBindError:
        return False
    except ldap3.LDAPException as e:
        raise e


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    wrong_login = False

    if form.validate_on_submit():
        user = User.query.filter_by(login=form.login.data).first()
        ldap_user = check_ldap_credentials(form.login.data, form.password.data)
        if user is not None and (pwd_context.verify(form.password.data, user.password) or ldap_user):
            if ldap_user:
                if user.display_name != ldap_user['display_name']:
                    user.display_name = ldap_user['display_name']
                    db.session.commit()
            login_user(user, remember=form.remember)
            identity_changed.send(current_app._get_current_object(),
                                  identity=Identity(user.id))
            flask.flash('Logged in successfully.')
            return form.redirect()
        else:
            wrong_login = True

    return render_template('login.html', form=form, wrong_login=wrong_login)


#@app.errorhandler(403)
def permission_denied_handler(e):
    print (e)
    if current_user.is_authenticated:
        return render_template('permission_denied.html')
    else:
        return redirect(url_for('login', next=request.url))


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
    identity.provides.add(RoleNeed("ANY"))


def get_or_create(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    else:
        instance = model(**kwargs)
        session.add(instance)
        session.commit()
        return instance


@app.before_first_request
def create_default_user():
    db.create_all()
    adm_role = get_or_create(db.session, Role, name='admin')
    dj_role = get_or_create(db.session, Role, name='dj')
    admin = get_or_create(db.session, User, login=config.admin_login)
    admin.password = pwd_context.encrypt(config.admin_password)
    admin.roles = [adm_role, dj_role]
    admin.active = True
    admin.commit = "admin z config.py, zawsze posiada hasło z config.py"
    db.session.commit()


def fix_chars(string):
    for char in CHAR_FIX:
        string = string.replace(char, CHAR_FIX[char])
    return string


def render_template_with_args(template, **kwargs):
    return render_template(template, radio_utils=radio_utils, version=__version__, **kwargs)


@app.route('/')
def ui_player():
    return render_template_with_args("player.html")


@app.route('/library/')
@library_browse_perm.require(http_exception=403)
def ui_library():
    return render_template_with_args("library_artists.html")


@app.route('/search/')
@library_browse_perm.require(http_exception=403)
def ui_library_search():
    query = request.args["q"]
    return render_template_with_args("library_search.html", query=query)


@app.route('/library/<artist>/')
@library_browse_perm.require(http_exception=403)
def ui_library_artist(artist):
    return render_template_with_args("library_artist_albums.html", artist=artist)


@app.route('/library/<artist>/<album>/')
@library_browse_perm.require(http_exception=403)
def ui_library_artist_album(artist, album):
    return render_template_with_args("library_artist_album_tracks.html", artist=artist, album=album)


@app.route('/api/v1/library/')
@library_browse_perm.require(http_exception=403)
def api_v1_library():
    return json.dumps(radio_utils.get_artists())


@app.route('/api/v1/library/<artist>/')
@library_browse_perm.require(http_exception=403)
def api_v1_library_artist(artist):
    return json.dumps(radio_utils.get_albums(artist))


@app.route('/api/v1/library/<artist>/<album>/')
@library_browse_perm.require(http_exception=403)
def api_v1_library_artist_album(artist, album):
    return json.dumps(radio_utils.get_tracks(artist, album))


@app.route('/api/v1/play_next/')
@music_control_perm.require(http_exception=403)
def api_v1_play_next():
    return json.dumps(radio_utils.play_next())


@app.route('/api/v1/play_prev/')
@music_control_perm.require(http_exception=403)
def api_v1_play_prev():
    return json.dumps(radio_utils.play_prev())


@app.route('/api/v1/pause/')
@music_control_perm.require(http_exception=403)
def api_v1_pause():
    return json.dumps(radio_utils.pause())


@app.route('/api/v1/vol/<value>/')
@music_control_perm.require(http_exception=403)
def api_v1_vol(value):
    return json.dumps(radio_utils.set_vol(value))


@app.route('/api/v1/status/')
def api_v1_status():
    return json.dumps(radio_utils.get_status())


@app.route('/api/v1/clear_q_and_play/<artist_id>/<album_id>/<track_id>/')
@music_control_perm.require(http_exception=403)
def api_v1_clear_q_and_play(artist_id, album_id, track_id):
    return json.dumps(radio_utils.clear_queue_and_play(artist_id, album_id, track_id))


@app.route('/api/v1/clear_queue/')
@music_control_perm.require(http_exception=403)
def api_v1_clear_queue():
    return json.dumps(radio_utils.clear_queue())


@app.route('/api/v1/add_to_q/<artist_id>/<album_id>/<track_id>/')
@music_control_perm.require(http_exception=403)
def api_v1_add_to_q(artist_id, album_id, track_id):
    return json.dumps(radio_utils.add_to_queue(artist_id, album_id, track_id))


@app.route('/api/v1/current_queue/')
def api_v1_current_queue():
    return json.dumps(radio_utils.get_current_queue())


@app.route('/api/v1/search_track/<query>')
@library_browse_perm.require(http_exception=403)
def api_v1_search_track(query):
    return json.dumps(radio_utils.search_for_track(query))


@app.route('/api/v1/albumart/<artist>/<album>/')
def api_v1_album_art(artist, album):
    url = ALBUM_ART_URL.format(unicode(fix_chars(artist).encode("utf-8")), PATTERN_FIX_ALBUM.sub("", unicode(fix_chars(album).encode("utf-8"))))
    return redirect(PATTERN_ALBUM_ART.findall(urlopen(url).read())[0], 302)


@app.route('/api/v1/play/')
@music_control_perm.require(http_exception=403)
def play():
    return json.dumps(radio_utils.play())

if __name__ == '__main__':
    app.debug = True
    app.run(host="0.0.0.0")
