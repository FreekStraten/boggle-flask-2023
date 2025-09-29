import os
import sqlite3

from flask import Flask, g, session, redirect, url_for, request

app = Flask(__name__)


# method for checking if a given username exists in the database
def check_user_exists(username):
    user = select_query('SELECT * FROM players WHERE name = ?', (username,))
    if user:
        return True
    else:
        return False


# method for getting the user ID of a given username
def get_user_id(username):
    user = select_query('SELECT * FROM players WHERE name = ?', (username,))
    if user:
        return user[0]['id']
    else:
        return None


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
        if row:
            return dict(row)
        else:
            return None


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
    db_path = os.path.join(app.root_path, 'boggle.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create tables
    cursor.execute('''
          CREATE TABLE IF NOT EXISTS players (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              name TEXT,
              score INTEGER
          )
      ''')

    cursor.execute('''
          CREATE TABLE IF NOT EXISTS games (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              player_id INTEGER,
              grid_size INTEGER,
              board_configuration TEXT,
              words_correct TEXT,
              completion_time FLOAT,
              FOREIGN KEY (player_id) REFERENCES players (id)
          )
      ''')

    # create a table that stores all guessed words for a game
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS guessed_words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id INTEGER,
                word TEXT,
                score INTEGER,
                FOREIGN KEY (game_id) REFERENCES games (id)
            )
        ''')

    # Commit the changes and close the connection
    conn.commit()
    conn.close()
