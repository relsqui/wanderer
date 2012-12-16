import random
from modules.constants import *
from modules import particles

class Player(object):
    """
    Data relating to the game player. Arguments:
        sprite  (sprites.Character)
        screen  (pygame.Surface inside which the player can move)
    """

    def __init__(self, sprite, screen):
        super(Player, self).__init__()
        self.area = screen.get_rect()
        self.sprite = sprite
        self.sprite.rect.center = self.area.center
        self.speed = PLAYER_SPEED
        self.last_greetings = [None for x in xrange(5)]

    def update(self):
        "Placeholder for when there's more to update."
        pass

    def move(self, direction):
        "Try to move in a direction."
        self.sprite.walk(direction)
        if direction is UP:
            vector = (0, -self.speed)
        elif direction is DOWN:
            vector = (0, self.speed)
        elif direction is LEFT:
            vector = (-self.speed, 0)
        else:
            vector = (self.speed, 0)
        newpos = self.sprite.rect.move(vector)
        if newpos.left > self.area.left and newpos.right < self.area.right and newpos.top > self.area.top and newpos.bottom < self.area.bottom:
            self.sprite.rect = newpos
        else:
            self.sprite.interject(random.choice(OUCHES))

    def greet(self):
        "Interject a random greeting."
        while True:
            greeting = random.choice(GREETINGS)
            if greeting not in self.last_greetings:
                self.last_greetings.pop(0)
                self.last_greetings.append(greeting)
                break
        self.sprite.interject(greeting)
