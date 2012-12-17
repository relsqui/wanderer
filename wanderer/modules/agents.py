import random, pygame
from modules.constants import *
from modules import particles, timers, sprites

class Agent(object):
    """
    Data relating to an agent (PC/NPC). Arguments:
        game            (game.Game object)
        name            (optional: string to call this agent)
        sprite          (optional: which # sprite to use, defaults to random)
        location        (optional: (x, y) location to center sprite on)
    """

    def __init__(self, game, name = "Anonymous Agent", spriteno = None, location = None):
        super(Agent, self).__init__()
        self.game = game
        self.name = name
        self.speed = PLAYER_SPEED

        self.last_greetings = [None for x in xrange(5)]
        self.interject_ok = True

        self.area = game.screen.get_rect()
        if spriteno:
            self.spriteno = spriteno
        else:
            self.spriteno = None
        self.set_sprite(location = location)

    def __repr__(self):
        return self.name

    def set_sprite(self, spriteno = None, location = None):
        if spriteno:
            self.spriteno = spriteno
        else:
            if self.spriteno:
                spriteno = self.spriteno
            else:
                self.spriteno = random.randint(1, 8)
                spriteno = self.spriteno
        spriteno = self.spriteno - 1
        column = spriteno % SHEET_COLUMNS
        row = spriteno / SHEET_COLUMNS
        charx = column * CHAR_WIDTH
        chary = row * CHAR_HEIGHT
        char_cursor = pygame.Rect(charx, chary, CHAR_WIDTH, CHAR_HEIGHT)
        sprite_sheet = pygame.image.load(LADY_SPRITES).convert()
        char_sheet = sprite_sheet.subsurface(char_cursor)
        if hasattr(self, "sprite"):
            if not location:
                location = self.sprite.rect
            direction = self.sprite.direction
            self.sprite.kill()
            self.sprite = sprites.Character(self, char_sheet, location, direction)
        elif not location:
            while True:
                locx = random.randrange(0, self.area.width - SPRITE_WIDTH)
                locy = random.randrange(0, self.area.height - SPRITE_HEIGHT)
                location = pygame.Rect(locx, locy, SPRITE_WIDTH, SPRITE_HEIGHT)
                self.sprite = sprites.Character(self, char_sheet, location)
                if not self.colliding():
                    break
                else:
                    self.sprite.kill()
        self.game.all_sprites.add(self.sprite)

    def update(self):
        "Placeholder for when there's more to update."
        pass

    def colliding(self):
        if self.colliding_wall():
            return True
        if self.colliding_sprites():
            return True
        return False

    def colliding_wall(self):
        if self.area.contains(self.sprite.rect):
            return False
        return True

    def colliding_sprites(self):
        all_other_sprites = self.game.all_sprites.sprites()
        if self.sprite in all_other_sprites:
            # It might not be, if we're just testing a potential position
            all_other_sprites.remove(self.sprite)
        collision_test = pygame.sprite.collide_mask
        collided_sprites = [s for s in all_other_sprites if collision_test(self.sprite, s)]
        # This is what pygame.sprite.spritecollide is for, but it wasn't working for some reason.
        if collided_sprites:
            return collided_sprites
        return False

    def move(self, direction, turn = True):
        "Try to move in a direction."
        self.sprite.walk(direction, turn)
        if direction is UP:
            vector = (0, -self.speed)
        elif direction is DOWN:
            vector = (0, self.speed)
        elif direction is LEFT:
            vector = (-self.speed, 0)
        else:
            vector = (self.speed, 0)
        oldpos = self.sprite.rect.copy()
        self.sprite.rect.move_ip(vector)
        if self.colliding():
            self.sprite.rect = oldpos
            return False
        return True

    def stop(self, direction = None):
        self.sprite.stand()

    def say(self, message):
        "Emit a message as a floating particle."
        offset = -1 * (self.sprite.rect.height/2 + FONT_SIZE/2 + 2)
        destination = self.sprite.rect.move(0, offset)
        self.game.all_particles.add(particles.TextParticle(self.game.font, message, destination))

    def interject(self, message):
        "Low-priority say(); discard if too frequent."
        if self.interject_ok:
            self.say(message)
            self.interject_ok = False
            timers.Timer(INTERJECT_TIMEOUT, self.reset_interject)

    def reset_interject(self):
        "Internal. Reset interjection timer."
        self.interject_ok = True

    def greet(self):
        "Interject a random greeting."
        while True:
            greeting = random.choice(GREETINGS)
            if greeting not in self.last_greetings:
                self.last_greetings.pop(0)
                self.last_greetings.append(greeting)
                break
        self.interject(greeting)


class Player(Agent):
    def colliding_wall(self):
        if super(Player, self).colliding_wall():
            self.interject(random.choice(OUCHES))
            return True
        return False

    def colliding_sprites(self):
        sprites = super(Player, self).colliding_sprites()
        if sprites:
            for sprite in sprites:
                sprite.agent.interject(random.choice(GREETINGS))
        return sprites


class Npc(Agent):
    def __init__(self, *args):
        super(Npc, self).__init__(*args)
        while self.spriteno == self.game.player.spriteno:
            self.spriteno = None
            self.set_sprite()
        self.speed = NPC_SPEED
        self.direction = None
        timers.Timer(1000, self.start_wandering)

    def update(self):
        if self.direction is not None:
            if not self.move(self.direction):
                self.direction = OPPOSITE[self.direction]

    def start_wandering(self):
        self.direction = random.choice(DIRECTIONS)
        timers.Timer(random.randint(MIN_WANDER, MAX_WANDER), self.stop_wandering)

    def stop_wandering(self):
        self.direction = None
        self.stop()
        timers.Timer(random.randint(MIN_WANDER, MAX_WANDER), self.start_wandering)
