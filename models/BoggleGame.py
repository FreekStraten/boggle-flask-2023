# boggle game model, contains all the game data
class BoggleGame:
    def __init__(self, board, words, player):
        self.board = board
        self.words = words
        self.player = player

    def __str__(self):
        return f"{self.board} {self.words} {self.player}"

    def __repr__(self):
        return f"{self.board} {self.words} {self.player}"

    def __eq__(self, other):
        return self.board == other.board and self.words == other.words and self.player == other.player

    def __ne__(self, other):
        return not self.__eq__(other)

