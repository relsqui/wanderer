import random
from modules.constants import *
from modules import particles

class Player(object):
    def __init__(self, sprite, font):
        super(Player, self).__init__()
        self.sprite = sprite
        self.font = font

    def update(self):
        pass

    def say(self, message):
        destination = self.sprite.rect.move(0, -20)
        return particles.TextParticle(self.font, message, destination)

    def greet(self):
        return self.say(random.choice(GREETINGS))
