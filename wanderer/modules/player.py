import random
from modules.constants import *
from modules import particles

class Player(object):
    def __init__(self, sprite, font):
        super(Player, self).__init__()
        self.sprite = sprite
        self.font = font
        self.last_greetings = [None, None, None]

    def update(self):
        pass

    def say(self, all_particles, message):
        offset = -1 * (self.sprite.rect.height/2 + FONT_SIZE/2 + 2)
        destination = self.sprite.rect.move(0, offset)
        all_particles.add(particles.TextParticle(self.font, message, destination))

    def greet(self, all_particles):
        while True:
            greeting = random.choice(GREETINGS)
            if greeting not in self.last_greetings:
                self.last_greetings.pop(0)
                self.last_greetings.append(greeting)
                break
        self.say(all_particles, greeting)
