import requests
import urllib.parse
import sqlite3

from urllib.parse import quote
from datetime import datetime, timedelta
from flask import Blueprint, redirect, request, jsonify, session, render_template, url_for, g

database = Blueprint(__name__, "database")
WEBSITE = 'http://192.168.15.151:5000/host'
CLIENT_ID = 'dce565a237ef49b680c53e1ee2db68e1'
CLIENT_SECRET = 'ed7f0355fe724b9b9be6489f5d8814f7'
REDIRECT_URI = WEBSITE + '/callback'
AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'
API_BASE_URL = 'https://api.spotify.com/v1/'

# Initialize the database
def init_db():
    with database.app_context():
        db = get_db()
        with database.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

# Connect to the database
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(database.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
    return g.db

@database.route('/')
def index():
    db = get_db()
    
    # Retrieve the currently playing information for display
    cur = db.execute('SELECT * FROM currently_playing WHERE user_id = ?', ('marijn-163',))
    current_playing_data = cur.fetchone()
    
    return render_template('index.html', current_playing_data=current_playing_data)

@database.route('/update_playing', methods=['POST'])
def update_playing():
    user_id = request.form.get('user_id')
    song_name = request.form.get('song_name')
    song_artist = request.form.get('song_artist')
    album_cover = request.form.get('album_cover')

    db = get_db()
    db.execute('INSERT OR REPLACE INTO currently_playing (user_id, song_name, song_artist, album_cover) VALUES (?, ?, ?, ?)',
               (user_id, song_name, song_artist, album_cover))
    db.commit()

    return 'OK'
