import json
import os
from time import timezone
from types import SimpleNamespace
from flask import Blueprint, render_template, request, redirect, url_for, g, session, flash
from database import select_query
from database import insert_query
import database as db
from auth import requires_auth
from models.Board import Board
from models.WordGuesser import WordGuesser
from datetime import datetime, timedelta, timezone

game = Blueprint('game', __name__)
app = game

# path to file containing all valid words, in the words folder
boggle_existing_words_path_nl = os.path.join(app.root_path, 'models/words/boggle_wordlist_NL.txt')
boggle_existing_words_path_en = os.path.join(app.root_path, 'models/words/boggle_wordlist_EN.txt')
currently_used_words_path = boggle_existing_words_path_en


@requires_auth
@game.route('/creategame', methods=['POST', 'GET'])
def create_game():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    if request.method == 'POST':
        board_size = request.form['board_size']
        amount_time = request.form['amount_time']
        lang = request.form['lang']

        if not board_size.isdigit() or not amount_time.isdigit():
            return render_template('boggle/creategame.html',
                                   error_message='Board size and amount time must be integers')

        board_size = int(board_size)
        amount_time = int(amount_time)

        try:
            font_size = 6 / board_size
            board = Board(board_size)
            processed_dice = [(i, die) for i, die in enumerate(board.board)]
        except ValueError:
            return render_template('boggle/creategame.html', error_message='Board size must be an integer')

        userid = session.get('user_id')
        if not userid:
            return render_template('boggle/creategame.html', error_message='User not logged in')

        if lang not in ('nl', 'en'):
            return render_template('boggle/creategame.html', error_message='Language must be "nl" or "en"')

        # Bewaar originele tijd in session (voor end-screen)
        session['initial_time'] = amount_time

        insert_query(
            'INSERT INTO games (player_id, grid_size, board_configuration, words_correct, completion_time, amount_time, lang) '
            'VALUES (?, ?, ?, ?, ?, ?, ?)',
            (userid, board_size, str(board.board), '', 0.0, amount_time, lang)
        )

        game_id = select_query('SELECT id FROM games WHERE player_id = ? ORDER BY id DESC LIMIT 1', (userid,))[0]['id']
        return redirect(url_for('game.boggle', game_id=game_id))
    else:
        return render_template('boggle/creategame.html')



@requires_auth
@game.route('/boggle/<int:game_id>', methods=['GET', 'POST'])
def boggle(game_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    # if the game is not in the database, redirect to the my_games page
    game_data = select_query('SELECT * FROM games WHERE id = ?', (game_id,))
    if not game_data or len(game_data) == 0:
        return redirect(url_for('game.my_games'))
    # if there is a score, the game has already ended so redirect to the ended game page
    # if game_data[0]['score'] != '':
    #     return redirect(url_for('game.end_game', game_id=game_id))

    # get all guessed words from the database
    guessed_words = select_query('SELECT * FROM guessed_words WHERE game_id = ?', (game_id,))

    if request.method == 'GET':
        game_data = select_query('SELECT * FROM games WHERE id = ?', (game_id,))
        if not game_data or len(game_data) == 0:
            flash('Invalid game ID', 'error')
            return redirect(url_for('game.my_games'))

        game_row = game_data[0]
        if len(game_row) < 6:
            flash('Invalid game data', 'error')
            return redirect(url_for('game.my_games'))

        session['game'] = {
            'id': game_row['id'],
            'player_id': game_row['player_id'],
            'grid_size': game_row['grid_size'],
            'board_configuration': game_row['board_configuration'],
            'words_correct': game_row['words_correct'],
            'completion_time': game_row['completion_time'],
            'selected_indexes': '',
            'amount_time': game_row['amount_time'],
            'lang': game_row['lang'],
        }

        evaluated_board = eval(session['game']['board_configuration'])
        session['processed_dice'] = [(i, die) for i, die in enumerate(evaluated_board)]
        session['font_size'] = 6 / session['game']['grid_size']
        session['board_size'] = session['game']['grid_size']
        session['game']['selected_indexes'] = json.dumps([])
        session['board'] = json.dumps(Board(session['game']['grid_size'], evaluated_board),
                                      default=lambda x: x.__dict__)
        session['start_time'] = datetime.now(timezone.utc)

        remaining_time = session['game']['amount_time'] - (datetime.now(timezone.utc) - session['start_time']).seconds

        return render_template('boggle/index.html', game=session['game'], dice=session['processed_dice'],
                               board_size=session['board_size'], font_size=session['font_size'],
                               current_word=json.loads(session['board'],
                                                       object_hook=lambda d: SimpleNamespace(**d)).current_word,
                               guessed_words=guessed_words, amount_time=remaining_time, lang=session['game']['lang'])

    if request.method == 'POST':
        jsonboard = json.loads(session['board'], object_hook=lambda d: SimpleNamespace(**d))
        board = Board(jsonboard.size, jsonboard.board)
        board.from_json(jsonboard)
        previous_indexes = json.loads(session['game'].get('selected_indexes', '[]'))
        board.set_previous_indexes(previous_indexes)
        position = int(request.form['position'])

        if 'previous_letters' in request.form:
            previous_letters = request.form['previous_letters']
        else:
            previous_letters = ''

        letter = board.board[position]

        if board.validate_move(position):
            previous_letters += letter
            previous_indexes.append(position)
            session['game']['selected_indexes'] = json.dumps(previous_indexes)

        session['board'] = json.dumps(board, default=lambda x: x.__dict__)
        previous_letters += letter
        previous_indexes = json.loads(session['game'].get('selected_indexes', '[]'))

        print("Amount of time:")
        print(session['game']['amount_time'])
        print("Time elapsed:")
        print((datetime.now(timezone.utc) - session['start_time']).seconds)

        remaining_time = session['game']['amount_time'] - (datetime.now(timezone.utc) - session['start_time']).seconds
        # save amount_time to the database
        insert_query('UPDATE games SET amount_time = ? WHERE id = ?', (remaining_time, game_id))

        return render_template('boggle/index.html', game=session['game'], dice=session['processed_dice'],
                               board_size=session['board_size'], font_size=session['font_size'],
                               current_word=board.current_word, previous_letters=previous_letters,
                               selected_positions=previous_indexes,
                               guessed_words=guessed_words, amount_time=remaining_time, lang=session['game']['lang'])


@requires_auth
@game.route('/boggle/<int:game_id>/submit', methods=['POST'])
def submit_word(game_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        raw_word = request.form.get('word', '')
        word = raw_word.strip()
        if not word:
            reset_current_selections()
            return redirect(url_for('game.boggle', game_id=game_id))

        duplicate = select_query(
            'SELECT 1 FROM guessed_words WHERE game_id = ? AND LOWER(word) = ? LIMIT 1',
            (game_id, word.lower())
        )
        if duplicate:
            reset_current_selections()
            return redirect(url_for('game.boggle', game_id=game_id))

        # Perform validation and scoring logic here
        score = validate_word(word)

        # add the word to the list of words found in the game database
        insert_query('INSERT INTO guessed_words (game_id, word, score) VALUES (?, ?, ?)', (game_id, word, score))

        reset_current_selections()

        # redirect to the game page
    return redirect(url_for('game.boggle', game_id=game_id))


@requires_auth
@game.route('/boggle/<int:game_id>/reset', methods=['POST'])
def reset_selections(game_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        # Reset the selected positions and current word
        reset_current_selections()
    return redirect(url_for('game.boggle', game_id=game_id))


@requires_auth
@game.route('/boggle/<int:game_id>/end', methods=['GET', 'POST'])
def end_game(game_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    guessed_words = select_query('SELECT * FROM guessed_words WHERE game_id = ?', (game_id,))
    game_data = select_query('SELECT * FROM games WHERE id = ?', (game_id,))
    if not game_data:
        flash('Invalid game ID', 'error')
        return redirect(url_for('game.my_games'))

    game_row = game_data[0]

    # Maak session['game'] opnieuw op (zoals in boggle())
    session['game'] = {
        'id': game_row['id'],
        'player_id': game_row['player_id'],
        'grid_size': game_row['grid_size'],
        'board_configuration': game_row['board_configuration'],
        'words_correct': game_row['words_correct'],
        'completion_time': game_row['completion_time'],
        'selected_indexes': '',
        'amount_time': game_row['amount_time'],
        'lang': game_row['lang']
    }

    evaluated_board = eval(session['game']['board_configuration'])
    session['processed_dice'] = [(i, die) for i, die in enumerate(evaluated_board)]
    session['font_size'] = 6 / session['game']['grid_size']
    session['board_size'] = session['game']['grid_size']
    session['game']['selected_indexes'] = json.dumps([])
    session['board'] = json.dumps(Board(session['game']['grid_size'], evaluated_board),
                                  default=lambda x: x.__dict__)

    # (we tonen de oorspronkelijke tijd in end-screen)
    def _fmt(sec):
        try:
            sec = int(sec)
        except Exception:
            sec = 0
        sec = max(0, sec)
        return f"{sec//60:02d}:{sec%60:02d}"

    # Prefer session value; fallback als die er niet is
    initial_time = session.get('initial_time')
    if initial_time is None:
        # laatste redmiddel: probeer completion_time + amount_time (kan afwijken)
        try:
            initial_time = int(game_row.get('completion_time') or 0) + int(game_row.get('amount_time') or 0)
        except Exception:
            initial_time = int(game_row.get('amount_time') or 0)
    initial_time_fmt = _fmt(initial_time)

    lang = session['game']['lang']
    word_magician = WordGuesser(language=lang, found_words=[w['word'].lower() for w in guessed_words])

    total_score = sum((w['score'] or 0) for w in guessed_words)

    if request.method == 'POST':
        # Markeer spel als beëindigd; completion_time hier laten staan zoals je hem gebruikt
        insert_query('UPDATE games SET has_ended = ?, score = ? WHERE id = ?',
                     (True, total_score, game_id))

    possible_words = word_magician.get_possible_words(session['game']['board_configuration'])

    # formatted_time is niet meer relevant; we tonen initial_time_fmt
    return render_template('boggle/endedgame.html',
                           game=session['game'],
                           dice=session['processed_dice'],
                           board_size=session['board_size'],
                           font_size=session['font_size'],
                           current_word=json.loads(session['board'],
                                                   object_hook=lambda d: SimpleNamespace(**d)).current_word,
                           guessed_words=guessed_words,
                           lang=session['game']['lang'],
                           possible_words=possible_words,
                           total_score=total_score,
                           initial_time_fmt=initial_time_fmt)


@requires_auth
@game.route('/mygames/')
def my_games():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    # Get all games for the current user
    all_games = select_query('SELECT * FROM games WHERE player_id = ?', (session['user_id'],))
    return render_template('boggle/mygames.html', games=all_games)


# Resets the current selections on the board
def reset_current_selections():
    session['game']['selected_indexes'] = json.dumps([])
    board = json.loads(session['board'], object_hook=lambda d: SimpleNamespace(**d))
    board.current_word = ''
    board.last_selected_letter_location = None
    session['board'] = json.dumps(board, default=lambda x: x.__dict__)


def validate_word(word):
    lang = session['game']['lang']
    w = WordGuesser(word, lang)
    return w.guess_word()
