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

    def say(self, all_particles, message):
        destination = self.sprite.rect.move(0, -20)
        all_particles.add(particles.TextParticle(self.font, message, destination))

    def greet(self, all_particles):
        self.say(all_particles, random.choice(GREETINGS))
