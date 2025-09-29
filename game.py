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

        # validate the request form that the size is an integer
        if not board_size.isdigit() and amount_time.isdigit():
            return render_template('boggle/creategame.html',
                                   error_message='Board size and amount time must be an integer')
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

        # check that lang is either 'nl' or 'en'
        if lang != 'nl' and lang != 'en':
            return render_template('boggle/creategame.html', error_message='Language must be either "nl" or "en"')

        # insert the new game into the database
        insert_query('INSERT INTO games (player_id, grid_size, board_configuration, '
                     'words_correct, completion_time, amount_time, lang) VALUES (?, ?, ?, ?, ?, ?, ?)',
                     (userid, board_size, str(board.board), '', 0.0, amount_time, lang))

        # redirect to the game page, of the game that was just created
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
        word = request.form['word']
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

        # get all guessed words from the database
    guessed_words = select_query('SELECT * FROM guessed_words WHERE game_id = ?', (game_id,))
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
        'lang': game_row['lang']
    }

    evaluated_board = eval(session['game']['board_configuration'])
    session['processed_dice'] = [(i, die) for i, die in enumerate(evaluated_board)]
    session['font_size'] = 6 / session['game']['grid_size']
    session['board_size'] = session['game']['grid_size']
    session['game']['selected_indexes'] = json.dumps([])
    session['board'] = json.dumps(Board(session['game']['grid_size'], evaluated_board),
                                  default=lambda x: x.__dict__)

    # Calculate the remaining time based on the start time and amount_time
    start_time = datetime.now()  # Set the start time when the game is started or created
    remaining_time = session['game']['amount_time'] - (datetime.now() - start_time).seconds

    lang = session['game']['lang']
    word_magician = WordGuesser(language=lang, found_words=guessed_words)
    possible_words = set()

    total_score = 0
    for word in guessed_words:
        total_score += word['score']

    # if it is a get request, get from the input field called amount
    if request.method == 'POST':
        # update the game in the db
        insert_query('UPDATE games SET completion_time = ?, has_ended = ?, score = ? WHERE id = ?',
                     (remaining_time, True, total_score, game_id))

        possible_words = word_magician.get_possible_words(session['game']['board_configuration'])
    else:
        possible_words = word_magician.get_possible_words(session['game']['board_configuration'], )

    return render_template('boggle/endedgame.html', game=session['game'], dice=session['processed_dice'],
                           board_size=session['board_size'], font_size=session['font_size'],
                           current_word=json.loads(session['board'],
                                                   object_hook=lambda d: SimpleNamespace(**d)).current_word,
                           guessed_words=guessed_words, amount_time=remaining_time,
                           possible_words=possible_words, lang=session['game']['lang'],
                           total_score=total_score)


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
