from flask import Blueprint, render_template, request, redirect, url_for, g, session

from database import select_query
from database import insert_query
import database as db

auth = Blueprint('auth', __name__)


def requires_auth(origfunc):
    def authenticator(*args, **kwargs):
        if 'user_name' in session:
            return origfunc(*args, **kwargs)
        session['nexturl'] = request.full_path.rstrip('?')
        return redirect(url_for('auth.login'))
    return authenticator


@auth.route('/users')
def users():
    all_users = select_query('SELECT * FROM players')
    return render_template('auth/users.html', users=all_users)


@auth.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']

        # Check if user exists in the database and validate the login session if they do
        user_exists = db.check_user_exists(username)
        if user_exists:
            # Validate login session
            # For example, you can store the user ID in the session
            session['user_id'] = db.get_user_id(username)
            g.user_name = username
            session['user_name'] = username
            return redirect(url_for('auth.users'))
        else:
            error_message = 'Invalid username'
            return render_template('auth/login.html', error_message=error_message)
    else:
        return render_template('auth/login.html')


@auth.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        name = request.form['username']
        score = request.form['score']
        insert_query('INSERT INTO players (name, score) VALUES (?, ?)', (name, score))
        return redirect(url_for('auth.users'))
    else:
        return render_template('auth/add_user.html')


@auth.route('/logout')
def logout():
    # Clear the session
    session.clear()
    return redirect(url_for('auth.login'))

