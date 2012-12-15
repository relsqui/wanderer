import os
from pygame.locals import *

# Window
WINDOW_SIZE = (500,400)
WINDOW_TITLE = "Wanderer"
BACKGROUND_COLOR = (50, 200, 70)

# Sprites
SPRITE_WIDTH = 32   # pixels
SPRITE_HEIGHT = 34  # pixels
CHAR_WIDTH = 96     # pixels
CHAR_HEIGHT = 136   # pixels
WALK_RATE = 250     # milliseconds between frames
SPRITE_SPEED = 2    # pixels per tick

# Controls
LEFT_KEYS = (K_h, K_LEFT)
RIGHT_KEYS = (K_l, K_RIGHT)
UP_KEYS = (K_k, K_UP)
DOWN_KEYS = (K_j, K_DOWN)
CONTROLS = (LEFT_KEYS, RIGHT_KEYS, UP_KEYS, DOWN_KEYS)
DOWN, LEFT, RIGHT, UP = (0, 1, 2, 3)

# Timeouts
PARTICLE_DEFAULT_TIMEOUT = 500  # milliseconds
TEXT_TIMEOUT_PER_CHAR = 150     # milliseconds

# Text
FONT_COLOR = (0, 0, 0)
FONT_SIZE = 20  # pixels
GREETINGS = []
f = open(os.path.join("data", "greetings.txt"))
for line in f:
    GREETINGS.append(line.strip())
f.close()
