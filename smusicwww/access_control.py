# -*- coding: utf-8 -*-
from flask import request, render_template, redirect, current_app, session, url_for
from werkzeug.routing import RequestRedirect
import flask
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin, \
    fresh_login_required, login_fresh
from flask_principal import Principal, Identity, AnonymousIdentity, identity_changed, identity_loaded, RoleNeed, \
    UserNeed, Permission
from flask_admin import Admin, AdminIndexView
import flask_admin
from flask_admin.contrib import sqla
import ldap3
from passlib.apps import custom_app_context as pwd_context

from forms import LoginForm
from shared import app, db
from utils import get_or_create, secure_random_string_generator
import config

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
    is_active = db.Column(db.Boolean())
    display_name = db.Column(db.String(255))
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))
    comment = db.Column(db.String(255))

    def __init__(self, login="none", password="", roles=None):
        if roles is None:
            roles = []
        self.login = login
        self.display_name = login
        if password == "":
            password = secure_random_string_generator(32)
        self.password = pwd_context.encrypt(password)
        self.is_active = True
        self.roles = roles

    def __str__(self):
        return "%s - %s - %s" % (self.id, self.login, self.display_name)


principals = Principal(app)
admin_perm = Permission(RoleNeed("admin"))
music_control_perm = Permission(RoleNeed("dj"))
library_browse_perm = Permission(RoleNeed("ANY"))
upload_perm = Permission(RoleNeed("dj"))

login_manager = LoginManager(app)
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.needs_refresh_message = (
    u"To protect your account, please reauthenticate to access this page."
)
login_manager.needs_refresh_message_category = "info"


class MyAdminIndexView(AdminIndexView):
    @flask_admin.expose('/')
    @admin_perm.require(http_exception=403)
    @fresh_login_required
    def index(self):
        return super(MyAdminIndexView, self).index()


admin = Admin(app, name='sMusic', index_view=MyAdminIndexView())


class UserAdmin(sqla.ModelView):
    form_columns = ['login', 'display_name', 'password', 'is_active', 'roles', 'comment']
    column_exclude_list = ['password']
    column_display_pk = False
    column_searchable_list = ('login', 'display_name')


admin.add_view(UserAdmin(User, db.session))


class RoleAdmin(sqla.ModelView):
    can_create = False
    can_delete = False
    form_columns = ['users']


admin.add_view(RoleAdmin(Role, db.session))


def check_ldap_credentials(username, password):
    try:
        conn = ldap3.Connection(ldap3.Server(config.ldap_host, use_ssl=True),
                                "cn=%s, cn=Users, dc=ad, dc=staszic, dc=waw, dc=pl" % username, password,
                                auto_bind=True, raise_exceptions=False)  # TODO: sprawdzić bezpieczeństwo połączenia
        ret = conn.search("cn=Users, dc=ad, dc=staszic, dc=waw, dc=pl", "(cn=%s)" % username,
                          attributes=['uidNumber', 'displayName'])
        if not ret:
            return False
        data = conn.entries
        if len(data) == 1:
            ldap_data = dict()
            ldap_data['login'] = username
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
    except ldap3.LDAPBindError, ldap3.LDAPSocketOpenError:
        return False
    except ldap3.LDAPException as e:
        raise e


def fill_database():
    admin_role = get_or_create(db.session, Role, name='admin')
    dj_role = get_or_create(db.session, Role, name='dj')
    admin_user = get_or_create(db.session, User, login=config.admin_login)
    admin_user.password = pwd_context.encrypt(config.admin_password)
    admin_user.roles = [admin_role, dj_role]
    admin_user.is_active = True
    admin_user.commit = "admin z config.py, zawsze posiada hasło z config.py"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    wrong_login = False

    if form.validate_on_submit():
        try:
            ldap_user = check_ldap_credentials(form.login.data, form.password.data)
        except ldap3.LDAPException as e:
            print e
            ldap_user = False
        user = User.query.filter_by(login=form.login.data).first()
        if user is None and ldap_user:
            new_user = User(login=form.login.data)
            new_user.comment = "Auto import from LDAP %s" % config.ldap_host
            db.session.add(new_user)
            db.session.commit()
            user = new_user
        if user is not None and (pwd_context.verify(form.password.data, user.password) or ldap_user or
                                 super_admin_can_check()):
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
    else:
        if hasattr(current_user, 'login'):
            form.login.data = current_user.login

    return render_template('login.html', form=form, wrong_login=wrong_login)


@login_manager.needs_refresh_handler
def refresh():
    return redirect(url_for('login', next=request.url))


@app.errorhandler(403)
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


@principals.identity_loader
def load_identity_when_session_expires():  # restores the identity when restoring from "remember me"
    if hasattr(current_user, 'id'):
        return Identity(current_user.id)


@identity_loaded.connect_via(app)
def on_identity_loaded(sender, identity):
    # Set the identity user object
    identity.user = current_user

    if hasattr(current_user, 'id'):
        identity.provides.add(UserNeed(current_user.id))

    if hasattr(current_user, 'roles'):
        for role in current_user.roles:
            identity.provides.add(RoleNeed(role.name))

    if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
        identity.provides.add(RoleNeed("ANY"))

    if hasattr(current_user, 'login') and current_user.login in config.super_admin:
        identity.provides.add(RoleNeed('super_admin'))
        for role in Role.query.all():
            identity.provides.add(RoleNeed(role.name))


def super_admin_can_check():
    if hasattr(current_user, 'login') and current_user.login in config.super_admin:
        if login_fresh():
            return True
        else:
            raise RequestRedirect(url_for('login', next=request.url))
    else:
        return False
