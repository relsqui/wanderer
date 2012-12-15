from pygame.locals import *

# Coordinate tuple indices
WIDTH = 0
HEIGHT = 1

# Window and other visual settings
WINDOW_SIZE = (600,200)
WINDOW_TITLE = "Hark! A turtle."
BACKGROUND_COLOR = (50, 200, 70)
TEXT_COLOR = (0, 0, 0)

# Controls
LEFT_KEYS = (K_h, K_LEFT)
RIGHT_KEYS = (K_l, K_RIGHT)
UP_KEYS = (K_k, K_UP)
DOWN_KEYS = (K_j, K_DOWN)
CONTROLS = (LEFT_KEYS, RIGHT_KEYS, UP_KEYS, DOWN_KEYS)
LEFT, RIGHT, UP, DOWN = (0, 1, 2, 3)

# Defaults
PARTICLE_DEFAULT_TIMEOUT = 3000 # milliseconds
PARTICLE_DEFAULT_FADE = 10      # steps
