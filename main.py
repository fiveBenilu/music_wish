from flask import Flask, request, render_template, redirect, url_for, session, abort, jsonify
from flask_socketio import SocketIO
from datetime import datetime, timedelta
from functools import wraps
import sqlite3
import os
from dotenv import load_dotenv
load_dotenv()
import requests

def genre_vorschlag(title, author):
    api_key = os.getenv("OPENROUTER_API_KEY")
    context_file = "event_config.txt"
    response = None

    if os.path.exists(context_file):
        with open(context_file, "r", encoding="utf-8") as f:
            context = f.read()
    else:
        context = ""

    prompt = f"""Eventbeschreibung & bevorzugte Genres: {context}

    Song: '{title}' von '{author}'

    Bewerte den Song im Kontext der Eventbeschreibung und prüf seine Eignung. Antworte danach ausschließlich mit genau einem Wort: entweder 'geeignet' oder 'ungeeignet'. Keine Erklärungen, kein Kontext, keine Einleitung. Nur dieses eine Wort."""

    api_key = os.getenv("NVIDIA_API_KEY")
    invoke_url = "https://integrate.api.nvidia.com/v1/chat/completions"
    stream = False

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "text/event-stream" if stream else "application/json"
    }

    payload = {
        "model": "meta/llama-3.3-70b-instruct",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 512,
        "temperature": 1.00,
        "top_p": 1.00,
        "frequency_penalty": 0.00,
        "presence_penalty": 0.00,
        "stream": stream
    }

    try:
        response = requests.post(invoke_url, headers=headers, json=payload)
        if response.ok:
            content = response.json()['choices'][0]['message']['content'].strip().lower()
            print("Antwort der KI:", content)
            if content == "ungeeignet":
                return "ungeeignet"
            elif content == "geeignet":
                return "geeignet"
            else:
                print("Unklare oder fehlerhafte Antwort:", content)
        else:
            print("Fehlerhafte Antwort:", response.text)
    except Exception as e:
        print(f"Fehler bei NVIDIA API: {e}")
        if response is not None:
            print("Fehlerhafte Antwort:", response.text)
    return "ungeeignet"


# KI-Begründung: Gibt einen Satz zurück, warum der Song geeignet/ungeeignet ist
def ki_begruendung(title, author):
    api_key = os.getenv("OPENROUTER_API_KEY")
    context_file = "event_config.txt"

    if os.path.exists(context_file):
        with open(context_file, "r", encoding="utf-8") as f:
            context = f.read()
    else:
        context = ""

    prompt = f"""Eventbeschreibung & bevorzugte Genres: {context}
# Gib einen geeigneten Alternativsong in dem Format "Ähnlicher geeigneter Titel: (Song - Interpret) \n                       ", wenn der Titel ungeeignet ist und begründe danach in einem Satz, warum der folgende Song für das Event geeignet oder ungeeignet ist:
'{title}' von '{author}'
"""

    api_key = os.getenv("NVIDIA_API_KEY")
    invoke_url = "https://integrate.api.nvidia.com/v1/chat/completions"
    stream = False

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "text/event-stream" if stream else "application/json"
    }

    payload = {
        "model": "meta/llama-3.3-70b-instruct",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 512,
        "temperature": 1.00,
        "top_p": 1.00,
        "frequency_penalty": 0.00,
        "presence_penalty": 0.00,
        "stream": stream
    }

    try:
        response = requests.post(invoke_url, headers=headers, json=payload)
        if response.ok:
            reason = response.json()['choices'][0]['message']['content'].strip()
            return reason
        else:
            print("Fehlerhafte Antwort:", response.text)
    except Exception as e:
        print(f"Fehler bei NVIDIA API: {e}")
        if response is not None:
            print("Fehlerhafte Antwort:", response.text)
    return "Limit"

app = Flask(__name__)
socketio = SocketIO(app)
app.secret_key = 'your_secret_key_here'

DB_PATH = 'wishes.db'

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS wishes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                title TEXT,
                author TEXT,
                comment TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                ip TEXT,
                classification TEXT DEFAULT 'offen'
            )
        ''')

# Direkt beim Modulstart Initialisierung der DB
init_db()

def get_client_ip():
    return request.headers.get('X-Forwarded-For', request.remote_addr)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        print("Formular-POST wurde empfangen")
        name = request.form['name']
        title = request.form['title']
        author = request.form['author']
        comment = request.form['comment']
        consent = request.form.get('consent')
        ip = get_client_ip()

        if not consent:
            return "Bitte Zustimmung zur Datenverarbeitung geben.", 400

        with sqlite3.connect(DB_PATH) as conn:
            conn.execute('''
                INSERT INTO wishes (name, title, author, comment, ip, classification)
                VALUES (?, ?, ?, ?, ?, 'offen')
            ''', (name, title, author, comment, ip))
            wish_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        klassifiziere_wunsch(wish_id, title, author)
        socketio.emit('update_wishes')

        return redirect(url_for('index', success='true'))

    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == 'passwort':
            session['admin_logged_in'] = True
            return redirect(url_for('admin'))
        else:
            return "Login fehlgeschlagen.", 401
    return render_template('login.html')

@app.route('/admin')
@login_required
def admin():
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute('SELECT id, name, title, author, comment, timestamp, classification FROM wishes').fetchall()
    return render_template('admin.html', wishes=rows)

@app.route('/delete/<int:wish_id>', methods=['POST'])
@login_required
def delete_wish(wish_id):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('DELETE FROM wishes WHERE id = ?', (wish_id,))
    return redirect(url_for('admin'))

@app.route('/admin/config', methods=['POST'])
@login_required
def update_config():
    config_text = request.form.get('event_config', '')
    with open("event_config.txt", "w", encoding="utf-8") as f:
        f.write(config_text)
    return redirect(url_for('admin'))

def klassifiziere_wunsch(wish_id, title, author):
    result = genre_vorschlag(title, author)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("UPDATE wishes SET classification = ? WHERE id = ?", (result, wish_id))


# Route für KI-Begründung abrufen
@app.route('/reason/<int:wish_id>')
@login_required
def reason(wish_id):
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute("SELECT title, author FROM wishes WHERE id = ?", (wish_id,)).fetchone()
        if not row:
            return jsonify({'reason': 'Nicht gefunden'}), 404
        title, author = row
        reason_text = ki_begruendung(title, author)
        if reason_text == "Limit":
            with sqlite3.connect(DB_PATH) as conn:
                #conn.execute("UPDATE wishes SET classification = ? WHERE id = ?", ("Limit", wish_id))
                pass
        return jsonify({'reason': reason_text})

# Chat-Antwort auf Musik- und DJ-Fragen
@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    messages = data.get('messages', [])
    if not messages:
        return jsonify({'response': 'Bitte stelle eine gültige Frage.'}), 400

    api_key = os.getenv("NVIDIA_API_KEY")
    invoke_url = "https://integrate.api.nvidia.com/v1/chat/completions"
    stream = False

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json"
    }

    payload = {
        "model": "meta/llama-3.3-70b-instruct",
        "messages": [{"role": "system", "content": "Du bist ein erfahrener DJ und Musikexperte. Antworte informativ, hilfreich und mit einem freundlichen Ton. Versuche dich außerdem kurz zu halten und antworte anhand von Fakten. Ich heiße Bennet also nenn mich auch so."}] + messages,
        "max_tokens": 500,
        "temperature": 0.9,
        "top_p": 1.0,
        "frequency_penalty": 0,
        "presence_penalty": 0,
        "stream": stream
    }

    try:
        response = requests.post(invoke_url, headers=headers, json=payload)
        if response.ok:
            content = response.json()['choices'][0]['message']['content'].strip()
            return jsonify({'response': content})
        else:
            print("Fehlerhafte Antwort:", response.text)
            return jsonify({'response': 'Fehler beim Abruf der KI-Antwort.'}), 500
    except Exception as e:
        print("Fehler bei Chat-Antwort:", e)
        return jsonify({'response': 'Fehler bei der Verarbeitung deiner Anfrage.'}), 500

if __name__ == '__main__':
    socketio.run(app, debug=True)
