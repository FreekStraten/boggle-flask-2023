# player model, contains all the player data
class Player:
    def __init__(self, username, score):
        self.username = username
        self.score = score
        self.id = id
        self.time = 1
        self.date = 1

    def __str__(self):
        return f"{self.username} {self.score} {self.time} {self.date}"

    def __repr__(self):
        return f"{self.username} {self.score} {self.time} {self.date}"

    def __eq__(self, other):
        return self.username == other.username and self.score == other.score and self.time == other.time and self.date == other.date

    def __ne__(self, other):
        return not self.__eq__(other)



