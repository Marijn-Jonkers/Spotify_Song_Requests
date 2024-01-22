import requests
import urllib.parse
import sqlite3

from urllib.parse import quote
from datetime import datetime, timedelta
from flask import Blueprint, redirect, request, jsonify, session, render_template, url_for

hosts = Blueprint(__name__, "hosts")
WEBSITE = 'http://192.168.15.151:5000/host'
CLIENT_ID = 'dce565a237ef49b680c53e1ee2db68e1'
CLIENT_SECRET = 'ed7f0355fe724b9b9be6489f5d8814f7'
REDIRECT_URI = WEBSITE + '/callback'
AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'
API_BASE_URL = 'https://api.spotify.com/v1/'

host = 0


@hosts.route('/')
def host():
    return render_template('host_page.html')

@hosts.route('/login')
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



@hosts.route('/callback')
def callback():
    global host
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
        host = 1

        return redirect('/dashboard')


@hosts.route('/dashboard')
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