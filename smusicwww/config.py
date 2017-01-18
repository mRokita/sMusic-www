"""
sMusic-www - config
"""
import ConfigParser
import os.path
import json
import datetime

conf = ConfigParser.ConfigParser()
config_paths = ["server.ini", "/etc/sMusic/server.ini", "/etc/sMusic/server.default.ini", "server.default.ini"]

found_config = False
for path in config_paths:
    if os.path.isfile(path):
        print "using config from: " + path
        conf.read(path)
        found_config = True
        break

if not found_config:
    print "ERROR! NO CONFIG FILE FOUND!!!"
    print "checked locations:" + "\n".join(config_paths)

listen_port = int(conf.get("Listen", "port"))
listen_host = conf.get("Listen", "host")
radio_key = conf.get("Security", "radio_key")
ssl_cert_file = conf.get("Security", "ssl_cert_file")
ssl_key_file = conf.get("Security", "ssl_key_file")
log_path = conf.get("Logs", "path")

virtualenv = conf.getboolean("WWW", "virtualenv")
admin_login = conf.get("WWW", "admin_login")
admin_password = conf.get("WWW", "admin_password")
super_admin = json.loads(conf.get("WWW", "super_admins"))
database_uri = conf.get("WWW", "database_uri")
secret_key = conf.get("Security", "secret_key")
ldap_host = conf.get("WWW", "ldap_server")

aktualizacja_last_seen = datetime.timedelta(seconds=int(conf.get("Server", "last_seen_update")))
timeout_time = datetime.timedelta(seconds=int(conf.get("Server", "timeout")))
ping_frequency = datetime.timedelta(seconds=int(conf.get("Server", "ping_interval")))
