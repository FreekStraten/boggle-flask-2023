from flask import Flask, render_template, request, redirect, url_for, g, blueprints, session
import pickle
from auth import auth
from game import game
from database import create_database

app = Flask(__name__)
app.register_blueprint(auth)
app.register_blueprint(game)


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')


@app.route('/debug', methods=['POST'])
def toggle_debug():
    if 'debug' in session:
        session.pop('debug')
    else:
        session['debug'] = True
    return redirect(url_for('index'))


if __name__ == '__main__':
    create_database()
    # app.secret_key = os.urandom(12)
    # for debugging, we use a static hard coded secret key
    app.secret_key = 'fiawhfiuawhfiowajofijwiof'
    app.run()
