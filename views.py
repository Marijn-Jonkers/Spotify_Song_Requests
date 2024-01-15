import requests
import urllib.parse

from urllib.parse import quote
from datetime import datetime, timedelta
from flask import Blueprint, redirect, request, jsonify, session, render_template, url_for

views = Blueprint(__name__, "views")
CLIENT_ID = 'dce565a237ef49b680c53e1ee2db68e1'
CLIENT_SECRET = 'ed7f0355fe724b9b9be6489f5d8814f7'
REDIRECT_URI = 'http://localhost:5000/callback'
AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'
API_BASE_URL = 'https://api.spotify.com/v1/'

@views.route('/')
def index():
    return render_template("index.html")

@views.route('/login')
def login():
    scope = 'user-read-email'

    params = {
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'scope': scope,
        'redirect_uri': REDIRECT_URI,
        'show_dialog': True
    }

    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"
    return redirect(auth_url)


@views.route('/callback')
def callback():
    if 'error' in request.args:
        return jsonify({"error": request.args['error']})

    if 'code' in request.args:
        req_body = {
            'code': request.args['code'],
            'grant_type': 'authorization_code',
            'redirect_uri': REDIRECT_URI,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }

        response = requests.post(TOKEN_URL, data=req_body)
        token_info = response.json()

        session['access_token'] = token_info['access_token']
        session['refresh_token'] = token_info['refresh_token']
        session['expires_at'] = datetime.now().timestamp() + token_info['expires_in']

        return redirect('/dashboard')
    


@views.route('/dashboard')
def dashboard():
    if 'access_token' not in session:
        return redirect('/login')

    if datetime.now().timestamp() > session['expires_at']:
        return redirect('/refresh-token')

    headers = {
        'Authorization': f"Bearer {session['access_token']}"
    }

    response = requests.get(API_BASE_URL + 'me', headers=headers)
    user_info = response.json()

    username = user_info['display_name']

    return render_template("dashboard.html", user_info=user_info, username=username)

@views.route('/request')
def request_page():
    if 'access_token' not in session:
        return redirect('/login')

    if datetime.now().timestamp() > session['expires_at']:
        return redirect('/refresh-token')

    headers = {
        'Authorization': f"Bearer {session['access_token']}"
    }

    return render_template("request.html")


@views.route('/submit_request', methods=['POST'])
def submit_request():
    artist = request.form.get('Artist')
    song = request.form.get('Song')

    if artist != '' and song != '':
        return redirect(url_for('views.artist_song_search', artist=artist, song=song))
    elif artist == '' and song != '':
        return redirect(url_for('views.song_search', song=song))
    elif artist != '' and song == '':
        return redirect(url_for('views.artist_search', artist=artist))
    else:
        return redirect('/no_search')


@views.route('/artist_song_search')
def artist_song_search():
    if 'access_token' not in session:
        return redirect('/login')

    if datetime.now().timestamp() > session['expires_at']:
        return redirect('/refresh-token')

    headers = {
        'Authorization': f"Bearer {session['access_token']}"
    }
    artist = request.args.get('artist')
    song = request.args.get('song')

    # Construct the query parameter with proper encoding
    query = f"q={quote(artist)}%20{quote(song)}&type=artist,track&limit=10"

    response = requests.get(API_BASE_URL + 'search?' + query, headers=headers)
    data = response.json()

    # Extract relevant information from the response
    songs = []
    for track in data.get('tracks', {}).get('items', []):
        song_info = {
            'title': track.get('name', 'Unknown Title'),
            'artist': ', '.join([artist['name'] for artist in track.get('artists', [])]),
            'album_cover': track.get('album', {}).get('images', [{}])[0].get('url', '')
        }
        songs.append(song_info)

    return render_template('request_list.html', artist=artist, song=song, songs=songs)



@views.route('/refresh-token')
def refresh_token():
    if 'refresh_token' not in session:
        return redirect('/login')

    if datetime.now().timestamp() > session['expires_at']:
        req_body = {
            'grant_type': 'refresh_token',
            'refresh_token': session['refresh_token'],
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }

        response = requests.post(TOKEN_URL, data=req_body)
        new_token_info = response.json()

        session['access_token'] = new_token_info['access_token']
        session['expires_at'] = datetime.now().timestamp() + new_token_info['expires_in']

        return redirect('/dashboard')

