import os
from pygame.locals import *

# Coordinate tuple indices
WIDTH = 0
HEIGHT = 1

# Window and other visual settings
WINDOW_SIZE = (500,400)
WINDOW_TITLE = "Hark! A turtle."
BACKGROUND_COLOR = (50, 200, 70)
FONT_COLOR = (0, 0, 0)
FONT_SIZE = 20

# Controls
LEFT_KEYS = (K_h, K_LEFT)
RIGHT_KEYS = (K_l, K_RIGHT)
UP_KEYS = (K_k, K_UP)
DOWN_KEYS = (K_j, K_DOWN)
CONTROLS = (LEFT_KEYS, RIGHT_KEYS, UP_KEYS, DOWN_KEYS)
LEFT, RIGHT, UP, DOWN = (0, 1, 2, 3)

# Defaults
PARTICLE_DEFAULT_TIMEOUT = 500  # milliseconds
TEXT_TIMEOUT_PER_CHAR = 150     # milliseconds

# Text
GREETINGS = []
f = open(os.path.join("data", "greetings"))
for line in f:
    GREETINGS.append(line.strip())
f.close()
