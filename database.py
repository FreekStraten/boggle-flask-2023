import os
import sqlite3

from flask import Flask, g

app = Flask(__name__)

# method for checking if a given username exists in the database
def check_user_exists(username):
    user = select_query('SELECT * FROM players WHERE name = ?', (username,))
    return bool(user)

# method for getting the user ID of a given username
def get_user_id(username):
    user = select_query('SELECT * FROM players WHERE name = ?', (username,))
    return user[0]['id'] if user else None

def next_row(generator):
    try:
        return dict(generator.__next__())
    except StopIteration:
        return {}

def select_query(query, bindings=None, select=True):
    conn = get_db()
    curs = conn.cursor()
    if bindings:
        curs.execute(query, bindings)
    else:
        curs.execute(query)

    if select:
        rows = curs.fetchall()
        return [dict(row) for row in rows]
    else:
        row = curs.fetchone()
        return dict(row) if row else None

def insert_query(query, bindings=None):
    conn = get_db()
    curs = conn.cursor()
    if bindings:
        curs.execute(query, bindings)
    else:
        curs.execute(query)
    conn.commit()

def connect_db():
    db_path = os.path.join(app.root_path, 'boggle.db')
    rv = sqlite3.connect(db_path)
    rv.row_factory = sqlite3.Row
    return rv

def get_db():
    if 'sqlite_db' not in g:
        g.sqlite_db = connect_db()
    return g.sqlite_db

@app.teardown_appcontext
def close_db(error):
    db = g.pop('sqlite_db', None)
    if db:
        db.close()

def create_database():
    """Create DB and ensure schema exists/migrates (incl. amount_time, lang, has_ended, score)."""
    db_path = os.path.join(app.root_path, 'boggle.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # players
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            score INTEGER
        )
    ''')

    # games (volledig schema)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER,
            grid_size INTEGER,
            board_configuration TEXT,
            words_correct TEXT,
            completion_time FLOAT,
            amount_time INTEGER,
            lang TEXT,
            has_ended INTEGER DEFAULT 0,
            score INTEGER DEFAULT 0,
            FOREIGN KEY (player_id) REFERENCES players (id)
        )
    ''')

    # guessed_words
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS guessed_words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id INTEGER,
            word TEXT,
            score INTEGER,
            FOREIGN KEY (game_id) REFERENCES games (id)
        )
    ''')

    # --- migratie voor bestaande DB's ---
    cursor.execute("PRAGMA table_info(games)")
    cols = [row[1] for row in cursor.fetchall()]
    if "amount_time" not in cols:
        cursor.execute("ALTER TABLE games ADD COLUMN amount_time INTEGER")
    if "lang" not in cols:
        cursor.execute("ALTER TABLE games ADD COLUMN lang TEXT")
    if "has_ended" not in cols:
        cursor.execute("ALTER TABLE games ADD COLUMN has_ended INTEGER DEFAULT 0")
    if "score" not in cols:
        cursor.execute("ALTER TABLE games ADD COLUMN score INTEGER DEFAULT 0")

    conn.commit()
    conn.close()

