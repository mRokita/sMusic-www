from flask import render_template
from __init__ import __version__


def render_template_with_args(template, **kwargs):
    return render_template(template, version=__version__, **kwargs)