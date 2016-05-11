# -*- coding: utf-8 -*-
from flask import request, render_template, redirect, current_app, session, url_for
import flask
from passlib.apps import custom_app_context as pwd_context

from forms import UploadForm
from shared import app
from access_control import upload_perm
import json
from flask_login import current_user

@app.route('/upload/', methods=['GET', 'POST'])
@upload_perm.require(http_exception=403)
def ui_upload():
    form = UploadForm()
    message = ""
    error = ""
    if form.validate_on_submit():
        artist = None
        if form.artist.data != "":
            artist = form.artist.data
        album = None
        if form.album.data != "":
            album = form.album.data
        track = None
        if form.track.data != "":
            track = form.track.data
        current_user.radio.add_download("youtube-dl", form.url.data, artist, album, track)
        message = "Dodano link do kolejki pobierania"

    return render_template('upload.html', form=form, message=message, error=error)


@app.route('/api/v1/current_download_queue/')
@upload_perm.require(http_exception=403)
def api_current_download_queue():
    return json.dumps(current_user.radio.get_current_dowanlod_queue())


@app.route('/api/v1/clear_download_queue/')
@upload_perm.require(http_exception=403)
def api_clear_download_queue():
    return json.dumps(current_user.radio.clear_download_queue())


@app.route('/api/v1/download_status/')
@upload_perm.require(http_exception=403)
def api_download_status():
    return json.dumps(current_user.radio.download_status())
