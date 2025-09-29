import math
import random
from .Dice import Dice


class Board:

    def __init__(self, size, board=None):
        if board is not None:
            self.board = board
            self.size = len(board)
        else:
            self.size = size ** 2
            self.board = self.create_board(self.size)
        self.last_selected_letter_location = None
        self.last_selected_letter = ""
        self.current_word = ""
        self.last_selected_indexes = []

    def create_board(self, size):
        die = [
            ['A', 'E', 'A', 'N', 'E', 'G'],
            ['A', 'H', 'S', 'P', 'C', 'O'],
            ['A', 'S', 'P', 'F', 'F', 'K'],
            ['O', 'B', 'J', 'O', 'A', 'B'],
            ['I', 'O', 'T', 'M', 'U', 'C'],
            ['R', 'Y', 'V', 'D', 'E', 'L'],
            ['L', 'R', 'E', 'I', 'X', 'D'],
            ['E', 'I', 'U', 'N', 'E', 'S'],
            ['W', 'N', 'G', 'E', 'E', 'H'],
            ['L', 'N', 'H', 'N', 'R', 'Z'],
            ['T', 'S', 'T', 'I', 'Y', 'D'],
            ['O', 'W', 'T', 'O', 'A', 'T'],
            ['E', 'R', 'T', 'T', 'Y', 'L'],
            ['T', 'O', 'E', 'S', 'S', 'I'],
            ['T', 'E', 'R', 'W', 'H', 'V'],
            ['N', 'U', 'I', 'H', 'M', 'Q']
        ]

        board = []
        for _ in range(size):
            dice_side = random.choice(die)
            board.append(Dice(dice_side).roll())

        return board

    def validate_move(self, position):
        # if the position is not set, then it is the first move.
        if self.last_selected_letter_location is None:
            self.last_selected_letter_location = position
            self.current_word += self.board[position]
            return True

        # if the position is in the last selected indexes, then it is a duplicate move
        if position in self.last_selected_indexes:
            return False

        size = math.sqrt(self.size)

        # check if the position is adjacent to the last selected letter
        last_row = self.last_selected_letter_location // size
        last_col = self.last_selected_letter_location % size

        row = position // size
        col = position % size

        row_diff = abs(row - last_row)
        col_diff = abs(col - last_col)

        # checks if the position is adjacent to the last selected letter
        if row_diff <= 1 and col_diff <= 1 and (row_diff + col_diff) != 0:
            self.current_word += self.board[position]
            self.last_selected_letter_location = position
            return True
        else:
            return False

    def from_json(self, json):
        self.board = json.board
        self.size = json.size
        self.last_selected_letter_location = json.last_selected_letter_location
        self.last_selected_letter = json.last_selected_letter
        self.current_word = json.current_word

    def set_previous_indexes(self, indexes):
        self.last_selected_indexes = indexes
