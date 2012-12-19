import os, sys
from pygame.locals import *

"""
Various constants for use in other modules.
"""

# General
DOWN, LEFT, RIGHT, UP = (0, 1, 2, 3)
DIRECTIONS = [DOWN, LEFT, RIGHT, UP]
OPPOSITE = [UP, RIGHT, LEFT, DOWN]
if getattr(sys, 'frozen', None):
    # BASEDIR = os.path.join(os.environ.get("_MEIPASS2", os.path.abspath(".")), "wanderer")
    BASEDIR = sys._MEIPASS
else:
    BASEDIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASEDIR, "data")

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
NPC_SPEED = 1       # pixels per tick
MIN_WANDER = 2000   # milliseconds (for NPC to pause or walk)
MAX_WANDER = 4000   # milliseconds (for NPC to pause or walk)
IMAGE_DIR = os.path.join(DATA_DIR, "images")
LADY_SPRITES = os.path.join(IMAGE_DIR, "lady_sprites.png")

# Controls
KEY_DELAY = 50
KEY_INTERVAL = 10
LEFT_KEYS = (K_h, K_LEFT, K_a)
RIGHT_KEYS = (K_l, K_RIGHT, K_d)
UP_KEYS = (K_k, K_UP, K_w)
DOWN_KEYS = (K_j, K_DOWN, K_s)
CONTROLS = (LEFT_KEYS, RIGHT_KEYS, UP_KEYS, DOWN_KEYS)

# Particles
PARTICLE_DEFAULT_TIMEOUT = 500  # milliseconds
FADE_STEPS = 5
FADE_AMOUNT = 255/FADE_STEPS

# Text
FONT_COLOR = (0, 0, 0)
FONT_SIZE = 8   # point
FONT_FILE = os.path.join(DATA_DIR, "04B_11__.TTF")
TEXT_TIMEOUT_PER_CHAR = 110      # milliseconds; this is for particles
INTERJECT_TIMEOUT = 500          # milliseconds; so is this
GREETINGS = []
OUCHES = []
CALLS = []
files = {}
files["greetings.txt"] = GREETINGS
files["ouches.txt"] = OUCHES
files["calls.txt"] = CALLS
TEXT_DIR = os.path.join(DATA_DIR, "text")
for filename, constant in files.items():
    f = open(os.path.join(TEXT_DIR, filename))
    for line in f:
        constant.append(line.strip())
    f.close()
