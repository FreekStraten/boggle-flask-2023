import random


class Dice:
    def __init__(self, sides, selected=False):
        self.sides = sides
        self.selected = selected

    def roll(self):
        return random.choice(self.sides)