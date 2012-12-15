import random
from modules.constants import *
from modules import particles

class Player(object):
    def __init__(self, sprite, font):
        super(Player, self).__init__()
        self.sprite = sprite
        self.font = font
        self.last_greetings = [None for x in xrange(5)]

    def update(self):
        pass

    def greet(self, all_particles):
        while True:
            greeting = random.choice(GREETINGS)
            if greeting not in self.last_greetings:
                self.last_greetings.pop(0)
                self.last_greetings.append(greeting)
                break
        self.sprite.say(all_particles, self.font, greeting)
