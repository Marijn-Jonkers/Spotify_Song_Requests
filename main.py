from flask import Flask
from views import views
from hosts import hosts
from database import database

import sqlite3


app = Flask(__name__)
app.secret_key = 'This is my secret key, do you like it?'
app.register_blueprint(views, url_prefix="/")
app.register_blueprint(hosts, url_prefix="/host")
app.register_blueprint(database, url_prefix="/database")
app.config['DATABASE'] = 'SpotifyPlayer.db'

WEBSITE = 'http://192.168.15.151:5000'
CLIENT_ID = 'dce565a237ef49b680c53e1ee2db68e1'
CLIENT_SECRET = 'ed7f0355fe724b9b9be6489f5d8814f7'
REDIRECT_URI = WEBSITE+'/callback'
AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'
API_BASE_URL = 'https://api.spotify.com/v1/'

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
