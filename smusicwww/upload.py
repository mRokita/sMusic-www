# -*- coding: utf-8 -*-
from flask import request, render_template, redirect, current_app, session, url_for
import flask
from passlib.apps import custom_app_context as pwd_context

from forms import UploadForm
from shared import app
from access_control import upload_perm


@app.route('/upload', methods=['GET', 'POST'])
@upload_perm.require(http_exception=403)
def ui_upload():
    form = UploadForm()
    message = ""
    if form.validate_on_submit():
        pass

    return render_template('upload.html', form=form, message=message)