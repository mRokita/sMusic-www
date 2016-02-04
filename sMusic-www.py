from functools import wraps
from flask import request, Response, Flask, render_template, redirect
import radio_utils
import json
import re
from urllib import urlopen, urlencode
app = Flask(__name__)

ALBUM_ART_URL = "http://www.slothradio.com/covers/?adv=0&artist={}&album={}"
PATTERN_ALBUM_ART = re.compile("\\<div class\\=\\\"album0\\\"\\>\\<img src\\=\\\"(.*?)\\\"")
PATTERN_FIX_ALBUM = re.compile("(\\ ?\\(.*?)\\)|(\\ ?[Dd][Ii][Ss][Cc] \d)|(\\ ?[Cc][Dd] \d)")

def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return username == 'admin' and password == 'secret'


def render_template_with_args(template, **kwargs):
    return render_template(template, radio_utils=radio_utils, **kwargs)


def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


@app.route('/')
@requires_auth
def hello_world():
    return render_template_with_args("index.html")


@app.route('/library/')
@requires_auth
def library():
    return render_template_with_args("library.html")


@app.route('/library/<artist>/')
@requires_auth
def library_artist(artist):
    return render_template_with_args("artist.html", artist=artist)


@app.route('/api/v1/library/<artist>/<album>/')
@requires_auth
def library_artist_album(artist, album):
    return json.dumps(radio_utils.get_tracks(artist, album))


@app.route('/api/v1/pause/')
@requires_auth
def pause():
    return json.dumps(radio_utils.pause())


@app.route('/ping')
@requires_auth
def ping():
    return "pong"


@app.route('/api/v1/vol/<value>/')
@requires_auth
def vol(value):
    return json.dumps(radio_utils.set_vol(value))


@app.route('/api/v1/status/')
@requires_auth
def status():
    return json.dumps(radio_utils.get_status())


@app.route('/api/v1/albumart/<artist>/<album>/')
@requires_auth
def album_art(artist, album):
    url = ALBUM_ART_URL.format(artist, PATTERN_FIX_ALBUM.sub("", album))
    return redirect(PATTERN_ALBUM_ART.findall(urlopen(url).read())[0], 302)


@app.route('/api/v1/play/')
@requires_auth
def play():
    return json.dumps(radio_utils.play())

if __name__ == '__main__':
    app.debug = True

    app.run(host="mrokita.pl")
