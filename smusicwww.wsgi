import sys
from smusicwww import config

if config.virtualenv:
    activate_this = "%s/bin/activate_this.py" % config.virtualenv
    execfile(activate_this, dict(__file__=activate_this))

from smusicwww.smusicwww import app as application
