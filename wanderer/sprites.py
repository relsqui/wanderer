import pygame, os, random
from wanderer import timers
from wanderer.constants import *


class Character(pygame.sprite.DirtySprite):
    """
    Animated character sprite. Arguments:
        agent           (agents.Agent this sprite belongs to)
        sheet           (pygame.Surface containing a sprite sheet)
        location        (pygame.Rect where the sprite should be)
        direction       (optional: which way the sprite should start facing)

    The sprite sheet will be chopped up and animated according to various layouts specs in the constants module.
    """

    WALK_RATE = 250     # milliseconds between animation frames

    def __init__(self, agent, sheet, location, direction = DOWN):
        super(Character, self).__init__()
        self.agent = agent
        self.sheet = sheet
        self.animations = []
        self.init_images()
        self.rect = location
        self.direction = direction
        self.animation = self.animations[self.direction]
        self.agent.game.all_sprites.add(self)
        self.update()
        self.dirty = 1

    def __repr__(self):
        "Developer-facing string representation."
        return "{}'s sprite".format(self.agent)

    def init_images(self):
        "Internal. Initialize animation frames from sprite sheet."
        for direction in (DOWN, LEFT, RIGHT, UP):
            frames = []
            for position in xrange(3):
                cursor = pygame.Rect(position * SPRITE_WIDTH, direction * SPRITE_HEIGHT, SPRITE_WIDTH, SPRITE_HEIGHT)
                frames.append(self.sheet.subsurface(cursor))
            frames.append(frames[1])
            self.animations.append(Animation(frames, self.WALK_RATE))

    def update(self):
        "Update the sprite image."
        self.image = self.animation.image()

    def kill(self):
        self.animation.stop()
        super(Character, self).kill()

    def turn(self, direction):
        "Changes the orientation of the sprite."
        if self.direction != direction:
            self.direction = direction
            was_walking = self.animation.running
            self.animation.stop()
            self.animation = self.animations[direction]
            if was_walking:
                self.animation.start()

    def stand(self, direction = None):
        "Stops walking animation, and optionally faces the given direction."
        if direction is not None:
            self.turn(direction)
        self.animation.stop()

    def walk(self, direction, turn = True):
        "Starts walking animation, optionally facing the given direction."
        if turn:
            self.turn(direction)
        self.animation.start()


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
        self.timer = None
        if not colorkey:
            colorkey = self.frames[default].get_at((0,0))
        self.colorkey = colorkey

    def cycle(self):
        "Internal. Update the image, if running."
        if self.running:
            self.current = (self.current + 1) % len(self.frames)
            self.timer = timers.Timer(self.speed, self.cycle)

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
        if self.timer:
            self.timer.cancel()
