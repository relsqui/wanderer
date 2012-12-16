import pygame, os, random
from modules import particles, timers
from modules.constants import *

class Character(pygame.sprite.Sprite):
    """
    Animated character sprite. Arguments:
        sheet           (pygame.Surface containing a sprite sheet)
        font            (pygame.font.Font for use in speaking)
        all_particles   (list of all particles, for appending speech to)

    The sprite sheet will be chopped up and animated according to various layouts specs in the constants module.
    """
    def __init__(self, sheet, font, all_particles):
        super(Character, self).__init__()
        self.sheet = sheet
        self.animations = []
        self.init_images()
        self.direction = DOWN
        self.animation = self.animations[self.direction]
        self.update()
        self.rect = self.image.get_rect()

        self.font = font
        self.all_particles = all_particles
        self.interject_ok = True

    def init_images(self):
        "Internal. Initialize animation frames from sprite sheet."
        for direction in (DOWN, LEFT, RIGHT, UP):
            frames = []
            for position in xrange(3):
                cursor = pygame.Rect(position * SPRITE_WIDTH, direction * SPRITE_HEIGHT, SPRITE_WIDTH, SPRITE_HEIGHT)
                frames.append(self.sheet.subsurface(cursor))
            frames.append(frames[1])
            self.animations.append(Animation(frames, WALK_RATE))

    def update(self):
        "Update the sprite image."
        self.image = self.animation.image()

    def turn(self, direction):
        self.direction = direction
        self.animation = self.animations[direction]

    def stand(self, direction = None):
        if direction is not None:
            self.turn(direction)
        self.animation.stop()

    def walk(self, direction = None):
        if direction is not None:
            self.turn(direction)
        self.animation.start()

    def reset_interject(self):
        "Internal. Reset interjection timer."
        self.interject_ok = True

    def say(self, message):
        "Emit a message as a floating particle."
        offset = -1 * (self.rect.height/2 + FONT_SIZE/2 + 2)
        destination = self.rect.move(0, offset)
        self.all_particles.add(particles.TextParticle(self.font, message, destination))

    def interject(self, message):
        "Low-priority say(); discard if too frequent."
        if self.interject_ok:
            self.say(message)
            self.interject_ok = False
            timers.Timer(INTERJECT_TIMEOUT, self.reset_interject)


class Animation(object):
    """
    Animates a sprite using a list of frame surfaces. Arguments:
        frames      (list of pygame.Surfaces)
        speed       (milliseconds, how frequently frames should change)
        colorkey    ((R,G,B) transparency color; detected from frames if not present)
        default     (integer, index of frame to display when not animating)
    """

    def __init__(self, frames, speed, colorkey = None, default = 1):
        super(Animation, self).__init__()
        self.frames = frames
        self.speed = speed
        self.default = default
        self.current = default
        self.running = False
        if not colorkey:
            colorkey = self.frames[default].get_at((0,0))
        self.colorkey = colorkey

    def cycle(self):
        "Internal. Update the image, if running."
        if self.running:
            self.current = (self.current + 1) % len(self.frames)
            timers.Timer(self.speed, self.cycle)

    def image(self):
        "Retrieve a pygame.Surface of the current animation frame."
        image = self.frames[self.current]
        image.set_colorkey(self.colorkey)
        return image

    def start(self):
        "Start the animation."
        if not self.running:
            self.running = True
            self.cycle()

    def stop(self):
        "Pause the animation."
        self.running = False
        self.current = self.default
