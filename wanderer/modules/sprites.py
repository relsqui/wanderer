import pygame, os, random
from modules import particles, timers
from modules.constants import *

class Character(pygame.sprite.Sprite):
    """
    Animated character sprite. Arguments:
        screen          (pygame.Surface inside which the character can move)
        sheet           (pygame.Surface containing a sprite sheet)
        font            (pygame.font.Font for use in speaking)
        all_particles   (list of all particles, for appending speech to)

    The sprite sheet will be chopped up and animated according to various layouts specs in the constants module.
    """
    def __init__(self, screen, sheet, font, all_particles):
        super(Character, self).__init__()
        self.sheet = sheet
        self.animations = []
        self.init_images()
        self.animation = self.animations[DOWN]
        self.direction = DOWN
        self.update()

        self.velocity = (0,0)
        self.speed = SPRITE_SPEED

        self.screen = screen
        self.area = screen.get_rect()
        self.rect = self.image.get_rect()
        self.rect.center = self.area.center

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

    def move(self, direction):
        "Try to move in a direction."
        self.direction = direction
        self.animation = self.animations[direction]
        self.animation.start()
        if direction is UP:
            vector = (0, -self.speed)
        elif direction is DOWN:
            vector = (0, self.speed)
        elif direction is LEFT:
            vector = (-self.speed, 0)
        else:
            vector = (self.speed, 0)
        newpos = self.rect.move(vector)
        if newpos.left > self.area.left and newpos.right < self.area.right and newpos.top > self.area.top and newpos.bottom < self.area.bottom:
            self.rect = newpos
        else:
            self.interject(random.choice(OUCHES))
    
    def stop_animation(self):
        "Internal. Stops whichever animation is currently running."
        self.animation.stop()

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
