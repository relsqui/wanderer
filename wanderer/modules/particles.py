import pygame
from modules.constants import *
from modules import timers

class ParticleGroup(pygame.sprite.Group):
    def draw(self, screen):
        for particle in self.sprites():
            screen.blit(particle.surface, particle.rect)

class Particle(pygame.sprite.Sprite):
    """
    A temporary sprite which will disappear after a short time. Arguments:
        surface (pygames.Surface)
        location (pygames.Rect, will use center point)
        timeout (integer, milliseconds)
        fade (integer)
    """

    def __init__(self, surface, location, timeout = PARTICLE_DEFAULT_TIMEOUT, vector = (0,0), fade = False):
        super(Particle, self).__init__()
        self.surface = surface
        self.rect = surface.get_rect()
        self.rect.center = location.center
        self.surface.set_alpha(255)
        self.vector = vector
        if fade:
            fade_time = timeout/FADE_STEPS
            for i in xrange(FADE_STEPS - 1):
                timers.Timer((i+1) * fade_time, self.fade)
        timers.Timer(timeout, self.kill)

    def fade(self):
        self.surface.set_alpha(self.surface.get_alpha() - FADE_AMOUNT)

    def update(self):
        self.rect.move_ip(self.vector)


class TextParticle(Particle):
    """
    A particle of rendered text. Arguments:
        message (string)
        location (pygames.Rect, will use center point)
        timeout (integer, milliseconds)
        fade (boolean)
    """

    def __init__(self, font, message, location, timeout = None, vector = (0, -2), fade = True):
        text = font.render(message, False, FONT_COLOR)
        if timeout is None:
            timeout = len(message) * TEXT_TIMEOUT_PER_CHAR
        super(TextParticle, self).__init__(text, location, timeout, vector, fade)
