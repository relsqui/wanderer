import pygame
from modules.constants import *
from modules import game

all_particles = pygame.sprite.Group()

class Particle(pygame.sprite.Sprite):
    """
    A temporary sprite which will disappear after a short time. Arguments:
        surface (pygames.Surface)
        location (pygames.Rect)
        timeout (integer, milliseconds)
        fade (integer)
    """

    def __init__(self, surface, location, timeout = PARTICLE_DEFAULT_TIMEOUT, fade = PARTICLE_DEFAULT_FADE):
        super(Particle, self).__init__()
        self.fade = fade
        self.timeout = timeout
        self.countdown = self.timeout
        self.surface = surface
        self.rect = location

    def update(self):
        self.countdown -= game.clock.get_time()
        if self.countdown < 0:
            self.kill()


class TextParticle(Particle):
    """
    A particle of rendered text. Arguments:
        message (string)
        destination (pygames.Rect)
        timeout (integer, milliseconds)
        fade (integer)
    """

    def __init__(self, message, destination, timeout = None, fade = PARTICLE_DEFAULT_FADE):
        text = game.font.render(message, False, TEXT_COLOR)
        textpos = text.get_rect()
        textpos.centerx = destination.centerx
        textpos.centery = destination.centery
        if timeout is None:
            timeout = len(message) * TEXT_TIMEOUT_PER_CHAR
        super(TextParticle, self).__init__(text, textpos, timeout, fade)
