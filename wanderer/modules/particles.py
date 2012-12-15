import pygame
from modules.constants import *

class ParticleGroup(pygame.sprite.Group):
    def draw(self, screen):
        for particle in self.sprites():
            screen.blit(particle.surface, particle.rect)

class Particle(pygame.sprite.Sprite):
    """
    A temporary sprite which will disappear after a short time. Arguments:
        surface (pygames.Surface)
        location (pygames.Rect)
        timeout (integer, milliseconds)
        fade (integer)
    """

    def __init__(self, surface, location, timeout = PARTICLE_DEFAULT_TIMEOUT, fade = False):
        super(Particle, self).__init__()
        self.fade = fade
        self.timeout = timeout
        self.countdown = self.timeout
        self.surface = surface
        self.rect = location

    def update(self, loop_time):
        self.countdown -= loop_time
        if self.countdown < 0:
            self.kill()
        elif self.fade:
            self.surface.set_alpha(255 * self.countdown/self.timeout)


class TextParticle(Particle):
    """
    A particle of rendered text. Arguments:
        message (string)
        destination (pygames.Rect)
        timeout (integer, milliseconds)
        fade (boolean)
    """

    def __init__(self, font, message, destination, timeout = None, fade = True):
        text = font.render(message, False, FONT_COLOR)
        textpos = text.get_rect()
        textpos.centerx = destination.centerx
        textpos.centery = destination.centery
        if timeout is None:
            timeout = len(message) * TEXT_TIMEOUT_PER_CHAR
        super(TextParticle, self).__init__(text, textpos, timeout, fade)
