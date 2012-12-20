import random, pygame
from wanderer.constants import *
from wanderer import particles, timers, sprites

class Agent(object):
    """
    Data relating to an agent (PC/NPC). Arguments:
        game            (game.Game object)
        name            (optional: string to call this agent)
        spriteno        (optional: which # sprite to use, defaults to random)
        location        (optional: (x, y) location to center sprite on)
    """

    def __init__(self, game, name = "Anonymous Agent", spriteno = None, location = None):
        super(Agent, self).__init__()
        self.game = game
        self.TEXT = self.game.TEXT
        self.game.all_agents.append(self)
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
        sprite_sheet = pygame.image.load(self.game.SPRITES).convert()
        char_sheet = sprite_sheet.subsurface(char_cursor)
        if hasattr(self, "sprite"):
            if not location:
                location = self.sprite.rect
            direction = self.sprite.direction
            self.sprite.kill()
            self.sprite = sprites.Character(self, char_sheet, location, direction)
        elif not location:
            old_iok = self.interject_ok
            self.interject_ok = False
            # To keep agents from responding to collisions while testing locations
            while True:
                locx = random.randrange(0, self.area.width - SPRITE_WIDTH)
                locy = random.randrange(0, self.area.height - SPRITE_HEIGHT)
                location = pygame.Rect(locx, locy, SPRITE_WIDTH, SPRITE_HEIGHT)
                self.sprite = sprites.Character(self, char_sheet, location)
                if not self.colliding():
                    break
                else:
                    self.sprite.kill()
            self.interject_ok = old_iok
        self.game.all_sprites.add(self.sprite)

    def update(self):
        "Placeholder for overriding."
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
        return collided_sprites

    def towards(self, target):
        targetx, targety = target.center
        selfx, selfy = self.sprite.rect.center
        if abs(selfx - targetx) > abs(selfy - targety):
            if targetx < selfx:
                facing = LEFT
            else:
                facing = RIGHT
        else:
            if targety < selfy:
                facing = UP
            else:
                facing = DOWN
        return facing

    def walk(self, direction, turn = True):
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

    def stand(self, direction = None):
        self.sprite.stand()

    def turn(self, direction):
        self.sprite.turn(direction)

    def say(self, message, font = None):
        "Emit a message as a floating particle."
        if font is None:
            font = self.game.font
        offset = -1 * (self.sprite.rect.height/2 + FONT_SIZE/2 + 2)
        location = self.sprite.rect.move(0, offset)
        self.game.all_particles.add(particles.TextParticle(font, message, location))

    def interject(self, message, font = None):
        "Low-priority say(); discard if too frequent."
        if self.interject_ok:
            self.say(message, font)
            self.interject_ok = False
            timers.Timer(INTERJECT_TIMEOUT, self.reset_interject)

    def reset_interject(self):
        "Internal. Reset interjection timer."
        self.interject_ok = True

    def greet(self, font = None):
        "Interject a random greeting."
        while True:
            greeting = random.choice(self.TEXT["greetings"])
            if greeting not in self.last_greetings:
                self.last_greetings.pop(0)
                self.last_greetings.append(greeting)
                break
        self.interject(greeting, font)


class Player(Agent):
    def colliding_wall(self):
        if super(Player, self).colliding_wall():
            self.interject(random.choice(self.TEXT["ouches"]))
            return True
        return False

    def colliding_sprites(self):
        sprites = super(Player, self).colliding_sprites()
        if sprites:
            for sprite in sprites:
                if isinstance(sprite.agent, Npc) and sprite.agent.is_startleable:
                    timers.Timer(100, sprite.agent.startled, self)
                    # this gives us time to finish the loop and uncollide
        return sprites

    def greet(self, font = None):
        super(Player, self).greet(font)
        audible = pygame.sprite.collide_circle_ratio(2)
        earshot = [npc for npc in self.game.all_npcs if audible(self.sprite, npc.sprite)]
        for npc in earshot:
            npc.greeted()

    def call(self, font = None):
        if font is None:
            font = self.game.big_font
        self.interject(random.choice(self.TEXT["calls"]), font)
        for npc in self.game.all_npcs:
            npc.called(self)


class Npc(Agent):
    def __init__(self, *args):
        super(Npc, self).__init__(*args)
        if len(self.game.all_agents) < 8:
            in_use = [a.spriteno for a in self.game.all_agents]
            while self.spriteno in in_use:
                self.spriteno = None
                self.set_sprite()
        self.game.all_npcs.append(self)
        self.speed = NPC_SPEED
        self.direction = None
        self.is_startleable = True
        self.timer = timers.Timer(random.randint(MIN_STARTWANDER, MAX_STARTWANDER), self.start_wandering)

    def update(self):
        if self.direction is not None:
            if not self.walk(self.direction):
                self.direction = OPPOSITE[self.direction]

    def colliding_sprites(self):
        sprites = super(Npc, self).colliding_sprites()
        if sprites:
            self.interject("Pardon me.")
        return sprites

    def start_wandering(self):
        self.direction = random.choice(DIRECTIONS)
        self.timer = timers.Timer(random.randint(MIN_WANDER, MAX_WANDER), self.stop_wandering)

    def stop_wandering(self):
        self.stand()
        self.direction = None
        self.timer = timers.Timer(random.randint(MIN_STAND, MAX_STAND), self.start_wandering)

    def greeted(self):
        timers.Timer(random.randint(MIN_GREETRESPONSE, MAX_GREETRESPONSE), self.greet)

    def called(self, caller):
        self.pause()
        self.turn(self.towards(caller.sprite.rect))

    def startled(self, startler):
        self.is_startleable = False
        self.pause()
        facing = self.towards(startler.sprite.rect)
        self.turn(facing)
        self.walk(OPPOSITE[facing], False)
        timers.Timer(100, self.reset_startled)
        # no random here, because it's just to account for keyrepeat

    def reset_startled(self):
        self.stand()
        self.is_startleable = True

    def pause(self, duration = None):
        if duration is None:
            duration = random.randint(MIN_PAUSE, MAX_PAUSE)
        self.direction = None
        self.stand()
        self.timer.cancel()
        self.timer = timers.Timer(duration, self.start_wandering)
