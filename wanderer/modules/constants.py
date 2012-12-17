import os
from pygame.locals import *

"""
Various constants for use in other modules.
"""

# General
DOWN, LEFT, RIGHT, UP = (0, 1, 2, 3)

# Window
WINDOW_HEIGHT = 250 # pixels
WINDOW_WIDTH = 300  # pixels
WINDOW_SIZE = (WINDOW_WIDTH, WINDOW_HEIGHT)
WINDOW_TITLE = "Wanderer"
BACKGROUND_COLOR = (50, 200, 70)

# Sprites
SPRITE_WIDTH = 32   # pixels
SPRITE_HEIGHT = 34  # pixels
CHAR_WIDTH = 96     # pixels
CHAR_HEIGHT = 136   # pixels
SHEET_ROWS = 2
SHEET_COLUMNS = 4
WALK_RATE = 250     # milliseconds between animation frames
PLAYER_SPEED = 3    # pixels per tick
LADY_SPRITES = os.path.join("images", "lady_sprites.png")

# Controls
KEY_DELAY = 50
KEY_INTERVAL = 10
LEFT_KEYS = (K_h, K_LEFT)
RIGHT_KEYS = (K_l, K_RIGHT)
UP_KEYS = (K_k, K_UP)
DOWN_KEYS = (K_j, K_DOWN)
CONTROLS = (LEFT_KEYS, RIGHT_KEYS, UP_KEYS, DOWN_KEYS)

# Timers
PARTICLE_DEFAULT_TIMEOUT = 500  # milliseconds
TEXT_TIMEOUT_PER_CHAR = 80      # milliseconds
INTERJECT_TIMEOUT = 500         # milliseconds
FADE_STEPS = 5
FADE_AMOUNT = 255/FADE_STEPS

# Text
FONT_COLOR = (0, 0, 0)
FONT_SIZE = 20  # pixels
GREETINGS = []
OUCHES = []
files = {"greetings.txt":GREETINGS, "ouches.txt":OUCHES}
for filename, constant in files.items():
    f = open(os.path.join("data", filename))
    for line in f:
        constant.append(line.strip())
    f.close()
