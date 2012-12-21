import pygame
from wanderer import timers

class Particle(pygame.sprite.DirtySprite):
    """
    A temporary sprite which will disappear after a short time. Arguments:
        surface     (pygames.Surface, particle contents)
        location    (pygames.Rect, particle will be centered on it)
        timeout     (milliseconds)
        vector      ((x, y) integer tuple, defaults to (0,0) for no movement)
        fade        (boolean, defaults to False)
    """

    PARTICLE_DEFAULT_TIMEOUT = 500  # milliseconds
    FADE_STEPS = 5
    FADE_AMOUNT = 255/FADE_STEPS

    def __init__(self, surface, location, timeout = None, vector = (0,0), fade = False):
        super(Particle, self).__init__()
        if timeout is None:
            timeout = self.PARTICLE_DEFAULT_TIMEOUT
        self.image = surface
        self.rect = surface.get_rect()
        self.rect.center = location.center
        self.image.set_alpha(255)
        self.dirty = 1
        self.vector = vector
        if fade:
            fade_time = timeout/self.FADE_STEPS
            for i in xrange(self.FADE_STEPS - 1):
                timers.Timer((i+1) * fade_time, self.fade)
        timers.Timer(timeout, self.kill)

    def fade(self):
        "Internal. Change the particle transparency."
        self.image.set_alpha(self.image.get_alpha() - self.FADE_AMOUNT)

    def update(self):
        "Update the particle position."
        self.rect.move_ip(self.vector)


class TextParticle(Particle):
    """
    A particle of rendered text. See Particle for arguments. Defaults to a vector of (0, -2), with fading, and will automatically calculate a timeout from string length if none is provided.
    """

    FONT_COLOR = (0, 0, 0)
    TEXT_TIMEOUT_PER_CHAR = 110 # milliseconds
    # size settings are in game.Game

    def __init__(self, font, message, location, timeout = None, vector = (0, -1), fade = True):
        text = font.render(message, False, self.FONT_COLOR)
        if timeout is None:
            timeout = len(message) * self.TEXT_TIMEOUT_PER_CHAR
        super(TextParticle, self).__init__(text, location, timeout, vector, fade)
