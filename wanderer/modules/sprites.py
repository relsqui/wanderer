import pygame, os
from modules import particles
from modules.constants import *

class Character(pygame.sprite.Sprite):
    def __init__(self, screen, sheet, font, all_particles):
        super(Character, self).__init__()
        self.sheet = sheet
        self.animations = []
        self.init_images()
        self.turn(DOWN)
        self.image = self.animation.image()

        self.velocity = (0,0)
        self.speed = SPRITE_SPEED

        self.screen = screen
        self.area = screen.get_rect()
        self.rect = self.image.get_rect()
        self.rect.center = self.area.center

        self.font = font
        self.all_particles = all_particles

    def init_images(self):
        for direction in (DOWN, LEFT, RIGHT, UP):
            frames = []
            for position in xrange(3):
                cursor = pygame.Rect(position * SPRITE_WIDTH, direction * SPRITE_HEIGHT, SPRITE_WIDTH, SPRITE_HEIGHT)
                frames.append(self.sheet.subsurface(cursor))
            frames.append(frames[1])
            self.animations.append(Animation(frames, WALK_RATE))

    def update(self, loop_time):
        if self.velocity == (0,0):
            self.animation.stop()
            self.position = 1
        else:
            self.animation.start()
            angle = self.velocity
            if self.velocity[0] and self.velocity[1]:
                if self.direction in (LEFT, RIGHT):
                    angle = (self.velocity[0], 0)
                else:
                    angle = (0, self.velocity[1])
            elif self.velocity[0]:
                if self.velocity[0] > 0:
                    self.turn(RIGHT)
                else:
                    self.turn(LEFT)
            elif self.velocity[1]:
                if self.velocity[1] > 0:
                    self.turn(DOWN)
                else:
                    self.turn(UP)
            newpos = self.rect.move(angle)
            if newpos.left > self.area.left and newpos.right < self.area.right and newpos.top > self.area.top and newpos.bottom < self.area.bottom:
                self.rect = newpos
        self.image = self.animation.image(loop_time)


    def move(self, direction):
        self.turn(direction)
        self.accelerate(direction)

    def turn(self, direction):
        self.direction = direction
        self.animation = self.animations[direction]

    def accelerate(self, direction, to_stop = False):
        xvel, yvel = self.velocity
        if direction is LEFT:
            if xvel or not to_stop:
                xvel -= self.speed
        elif direction is RIGHT:
            if xvel or not to_stop:
                xvel += self.speed
        elif direction is UP:
            if yvel or not to_stop:
                yvel -= self.speed
        elif direction is DOWN:
            if yvel or not to_stop:
                yvel += self.speed
        xvel = min(xvel, self.speed)
        xvel = max(xvel, -1 * self.speed)
        yvel = min(yvel, self.speed)
        yvel = max(yvel, -1 * self.speed)
        self.velocity = (xvel, yvel)
    
    def say(self, message):
        offset = -1 * (self.rect.height/2 + FONT_SIZE/2 + 2)
        destination = self.rect.move(0, offset)
        self.all_particles.add(particles.TextParticle(self.font, message, destination))


class Animation(object):
    def __init__(self, frames, speed, colorkey = None, default = 1):
        super(Animation, self).__init__()
        self.frames = frames
        self.speed = speed
        self.default = default
        self.current = default
        self.countdown = speed
        self.running = False
        if not colorkey:
            colorkey = self.frames[default].get_at((0,0))
        self.colorkey = colorkey

    def update(self, loop_time):
        if self.running:
            self.countdown -= loop_time
            if self.countdown <= 0:
                self.current = (self.current + 1) % len(self.frames)
                self.countdown = self.speed

    def image(self, loop_time = 0):
        if loop_time:
            self.update(loop_time)
        image = self.frames[self.current]
        image.set_colorkey(self.colorkey)
        return image

    def start(self):
        self.running = True

    def stop(self):
        self.running = False
        self.current = self.default
