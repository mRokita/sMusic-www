from functools import wraps
from flask import request, Response, Flask, render_template, redirect
import radio_utils
app = Flask(__name__)


def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return username == 'admin' and password == 'secret'

def render_template_with_args(template):
    return render_template(template, radio_utils=radio_utils)

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


@app.route('/pause')
@requires_auth
def pause():
    radio_utils.pause()
    return redirect('/')

@app.route('/vol/<value>')
def vol(value):
    radio_utils.set_vol(value)
    return redirect("/")

@app.route('/play')
@requires_auth
def play():
    radio_utils.play()
    return redirect('/')

if __name__ == '__main__':
    app.debug = True
    app.run(host="mrokita.pl")
