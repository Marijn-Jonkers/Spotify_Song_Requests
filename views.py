import requests
import urllib.parse
import sqlite3

from urllib.parse import quote
from datetime import datetime, timedelta
from flask import Blueprint, redirect, request, jsonify, session, render_template, url_for
from hosts import host

views = Blueprint(__name__, "views")
WEBSITE = 'http://192.168.15.151:5000'
CLIENT_ID = 'dce565a237ef49b680c53e1ee2db68e1'
CLIENT_SECRET = 'ed7f0355fe724b9b9be6489f5d8814f7'
REDIRECT_URI = WEBSITE + '/callback'
AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'
API_BASE_URL = 'https://api.spotify.com/v1/'


@views.route('/')
def index():
    if host == 1:
        return redirect('/dashboard')
    else:
        return redirect('/user_login')

@views.route('/user_login')
def user_login():
    return render_template('login.html')

@views.route('/login')
def login():
    scope = ' user-read-private user-read-email user-read-playback-state user-read-currently-playing'

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
        return redirect('/')

    if datetime.now().timestamp() > session['expires_at']:
        return redirect('/refresh-token')

    headers = {
        'Authorization': f"Bearer {session['access_token']}"
    }

    response = requests.get(API_BASE_URL + 'me', headers=headers)
    user_info = response.json()

    username = user_info['display_name']

    return render_template("dashboard.html", user_info=user_info, username=username)


@views.route('/currently-playing-json')
def currently_playing_json():
    if 'access_token' not in session:
        return redirect('/login')

    if datetime.now().timestamp() > session['expires_at']:
        return redirect('/refresh-token')

    headers = {
        'Authorization': f"Bearer {session['access_token']}"
    }

    player_status = requests.get(API_BASE_URL + 'me/player', headers=headers)

    if player_status.status_code == 200 and player_status.json().get('is_playing', False):
        playing = requests.get(API_BASE_URL + 'me/player/currently-playing', headers=headers)

        if playing.status_code == 200:
            now_playing = playing.json()
            song_name = now_playing.get('item', {}).get('name', 'No song currently playing')
            song_artist = now_playing.get('item', {}).get('artists', [{}])[0].get('name', 'Unknown Artist')
            cover_image = now_playing.get('item', {}).get('album', {}).get('images', [{}])[0].get('url', '../static/img/white.png')

            update_playing_endpoint = '/update_playing'
            update_playing_data = {
                'user_id': 'marijn-163',
                'song_name': song_name,
                'song_artist': song_artist,
                'album_cover': cover_image
            }
            requests.post(WEBSITE + update_playing_endpoint, data=update_playing_data)
    else:
        song_name = 'No song currently playing'
        song_artist = 'Unknown Artist'
        cover_image = '../static/img/white.png'
    return jsonify({
        'song_name': song_name,
        'song_artist': song_artist,
        'cover_image': cover_image
    })



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

    if artist == '' and song == '':
        return redirect('/no_search')
    else:
        return redirect(url_for('views.artist_song_search', artist=artist, song=song))


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

    query = f"q={quote(artist)}%20{quote(song)}&type=artist,track&limit=10"

    response = requests.get(API_BASE_URL + 'search?' + query, headers=headers)
    data = response.json()

    songs = []
    for track in data.get('tracks', {}).get('items', []):
        song_info = {
            'title': track.get('name', 'Unknown Title'),
            'artist': ', '.join([artist['name'] for artist in track.get('artists', [])]),
            'album_cover': track.get('album', {}).get('images', [{}])[0].get('url', '')
        }
        songs.append(song_info)

    return render_template('request_list.html', artist=artist, song=song, songs=songs)


@views.route('/no_search')
def no_search():
    if 'access_token' not in session:
        return redirect('/login')

    if datetime.now().timestamp() > session['expires_at']:
        return redirect('/refresh-token')

    headers = {
        'Authorization': f"Bearer {session['access_token']}"
    }
    songs = []
    song_info = {
            'title': 'No song searched for',
            'artist': 'No artist searched for',
            'album_cover': ''
    }
    songs.append(song_info)

    return render_template('request_list.html', songs=songs)


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
