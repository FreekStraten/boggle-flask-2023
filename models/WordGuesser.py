import os
from difflib import SequenceMatcher
from itertools import product
import concurrent.futures
from flask import Flask, session

app = Flask(__name__)

# path to file containing all valid words, in the words folder
boggle_existing_words_path_nl = os.path.join(app.root_path, 'words/boggle_wordlist_NL.txt')
boggle_existing_words_path_en = os.path.join(app.root_path, 'words/boggle_wordlist_EN.txt')
currently_used_words_path = boggle_existing_words_path_en


class WordGuesser:

    def __init__(self, word=None, language="nl", found_words=None):
        self.word = word
        self.language = language
        self.text_path = self.set_text_path(language)
        self.wordlist = list()  # List of all existing words
        self.found_words = found_words

        self.load_wordlist()

    def load_wordlist(self):
        with open(self.text_path, 'r', encoding='utf-8') as f:
            # unieke, lowercase woorden en gesorteerd voor binary search & prefix checks
            self.wordlist = sorted({line.strip().lower() for line in f if line.strip()})

    def set_text_path(self, language):
        if language == "en":
            return boggle_existing_words_path_en
        elif language == "nl":
            return boggle_existing_words_path_nl
        else:
            raise ValueError("Language not supported")

    def guess_word(self):
        print(self.text_path)
        try:
            # get the text file containing all existing possible words in the words folder
            with open(self.text_path) as f:
                existing_words = [line.strip() for line in f]
                word = self.word.strip().lower()
                # use a complex algorithm to find the word in the list of existing words
                # if the word is found, return the score
                if word in existing_words:
                    print('Word found')
                    self.get_score()
                    print(self.get_score())
                    return self.get_score()
                else:
                    if 'debug' in session:
                        # print all similar words
                        print('Word not found')
                        print('Word: ' + word)
                        print('Similar words:')
                        for existing_word in existing_words:
                            if SequenceMatcher(None, word, existing_word).ratio() > 0.7:
                                print(existing_word)
                    return -1
        except:
            print('Error validating word')
            return 0

    def get_score(self):
        # Woord van 3 en 4 letters → 1 punt
        # Woord van 5 letters → 2 punten
        # Woord van 6 letters → 3 punten
        # Woord van 7 letters → 5 punten
        # Woord van 8 letter of meer → 11 punten

        # get the length of the word
        word_length = len(self.word)
        print(word_length)
        # return the score based on the length of the word
        if word_length == 3 or word_length == 4:
            return 1
        elif word_length == 5:
            return 2
        elif word_length == 6:
            return 3
        elif word_length == 7:
            return 5
        elif word_length >= 8:
            return 11
        else:
            return 0

    def get_possible_words(self, board_configuration):
        board = eval(board_configuration)
        size = int(len(board) ** 0.5)
        visited = [[False] * size for _ in range(size)]
        possible_words = set()

        alphabet_parts = self.split_alphabet()

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = []
            for part in alphabet_parts:
                futures.append(executor.submit(self.dfs_alphabet_part, board, size, part, "", visited, possible_words))

            # Wait for all threads to complete
            concurrent.futures.wait(futures)

        return list(possible_words)

    def split_alphabet(self):
        alphabet = "abcdefghijklmnopqrstuvwxyz"
        # The amount of letters per part
        num_parts = 8

        part_size = len(alphabet) // num_parts
        alphabet_parts = [alphabet[i:i + part_size] for i in range(0, len(alphabet), part_size)]
        return alphabet_parts

    def dfs_alphabet_part(self, board, size, alphabet_part, current_word, visited, possible_words):
        if not alphabet_part:
            return

        for i in range(size):
            for j in range(size):
                self.dfs(board, size, i, j, current_word, visited, possible_words, alphabet_part)

    def dfs(self, board, size, row, col, current_word, visited, possible_words, alphabet_part):
        if row < 0 or col < 0 or row >= size or col >= size or visited[row][col]:
            return

        current_word += board[row * size + col]
        if not self.is_prefix(current_word):
            return

        visited[row][col] = True

        # if there are more than 20 possible words, stop searching
        if len(possible_words) > 20:
            return

        if self.is_word(current_word, size):
            possible_words.add(current_word)

        for dr, dc in product([-1, 0, 1], repeat=2):
            if dr == 0 and dc == 0:
                continue

            new_row = row + dr
            new_col = col + dc
            self.dfs(board, size, new_row, new_col, current_word, visited, possible_words, alphabet_part)

        visited[row][col] = False

    def is_word(self, word, boardsize):
        if len(word) < 4 < boardsize:
            return False
        if word in self.found_words:
            return False
        return self.binary_search(word.lower()) != -1

    def is_prefix(self, prefix):
        return any(word.startswith(prefix.lower()) for word in self.wordlist)

    def binary_search(self, target):
        left = 0
        right = len(self.wordlist) - 1

        while left <= right:
            mid = (left + right) // 2
            mid_word = self.wordlist[mid] # This gives the error Class set does not define '__getitem__'

            if mid_word == target:
                return mid
            elif mid_word < target:
                left = mid + 1
            else:
                right = mid - 1

        return -1