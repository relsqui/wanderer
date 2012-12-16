import random, pygame
from modules.constants import *
from modules import particles, timers, sprites

class Player(object):
    """
    Data relating to the game player. Arguments:
        sprite          (sprites.Character)
        screen          (pygame.Surface inside which the player can move)
        font            (pygame.font.Font for use in speaking)
        all_particles   (list of all particles, for appending speech to)
    """

    def __init__(self, screen, font, all_particles):
        super(Player, self).__init__()
        self.area = screen.get_rect()
        self.set_sprite()
        self.sprite.rect.center = self.area.center

        self.speed = PLAYER_SPEED

        self.font = font
        self.last_greetings = [None for x in xrange(5)]
        self.interject_ok = True
        self.all_particles = all_particles

    def set_sprite(self, spriteno = 2):
        spriteno -= 1
        row = spriteno % SHEET_COLUMNS
        column = spriteno / SHEET_COLUMNS
        charx = row * CHAR_WIDTH
        chary = column * CHAR_HEIGHT
        char_cursor = pygame.Rect(charx, chary, CHAR_WIDTH, CHAR_HEIGHT)
        sprite_sheet = pygame.image.load(LADY_SPRITES).convert()
        char_sheet = sprite_sheet.subsurface(char_cursor)
        self.sprite = sprites.Character(char_sheet)

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
        if self.area.contains(newpos):
            self.sprite.rect = newpos
        else:
            self.interject(random.choice(OUCHES))

    def say(self, message):
        "Emit a message as a floating particle."
        offset = -1 * (self.sprite.rect.height/2 + FONT_SIZE/2 + 2)
        destination = self.sprite.rect.move(0, offset)
        self.all_particles.add(particles.TextParticle(self.font, message, destination))

    def interject(self, message):
        "Low-priority say(); discard if too frequent."
        if self.interject_ok:
            self.say(message)
            self.interject_ok = False
            timers.Timer(INTERJECT_TIMEOUT, self.reset_interject)

    def reset_interject(self):
        "Internal. Reset interjection timer."
        self.interject_ok = True

    def greet(self):
        "Interject a random greeting."
        while True:
            greeting = random.choice(GREETINGS)
            if greeting not in self.last_greetings:
                self.last_greetings.pop(0)
                self.last_greetings.append(greeting)
                break
        self.interject(greeting)
