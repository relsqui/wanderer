import random
from modules.constants import *
from modules import particles

class Player(object):
    """
    Data relating to the game player. Arguments:
        sprite  (sprites.Character)
    """

    def __init__(self, sprite):
        super(Player, self).__init__()
        self.sprite = sprite
        self.last_greetings = [None for x in xrange(5)]

    def update(self):
        "Placeholder for when there's more to update."
        pass

    def greet(self):
        "Interject a random greeting."
        while True:
            greeting = random.choice(GREETINGS)
            if greeting not in self.last_greetings:
                self.last_greetings.pop(0)
                self.last_greetings.append(greeting)
                break
        self.sprite.interject(greeting)
