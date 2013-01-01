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

    INTERJECT_TIMEOUT = 500     # milliseconds
    SPEED = 3                   # pixels per tick
    CHAR_WIDTH = 96             # pixels
    CHAR_HEIGHT = 136           # pixels
    SHEET_ROWS = 2
    SHEET_COLUMNS = 4

    def __init__(self, game, name = "Anonymous Agent", spriteno = None, location = None):
        super(Agent, self).__init__()
        self.game = game
        self.texts = self.game.texts
        self.game.all_agents.append(self)
        self.name = name
        self.speed = self.SPEED
        self.holding = None

        self.last_greetings = [None for x in xrange(5)]
        self.interject_ok = True

        self.area = game.screen.get_rect()
        if spriteno:
            self.spriteno = spriteno
        else:
            self.spriteno = None
        self.set_sprite(location = location)

    def __repr__(self):
        "Internal. Developer-facing string representation."
        return self.name

    def set_sprite(self, spriteno = None, location = None):
        "Internal. Create a sprite and associate it with this agent."
        if spriteno:
            self.spriteno = spriteno
        else:
            if self.spriteno:
                spriteno = self.spriteno
            else:
                self.spriteno = random.randint(1, 8)
                spriteno = self.spriteno
        spriteno = self.spriteno - 1
        column = spriteno % self.SHEET_COLUMNS
        row = spriteno / self.SHEET_COLUMNS
        charx = column * self.CHAR_WIDTH
        chary = row * self.CHAR_HEIGHT
        char_cursor = pygame.Rect(charx, chary, self.CHAR_WIDTH, self.CHAR_HEIGHT)
        sprite_sheet = pygame.image.load(self.game.sprites).convert()
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

    def update(self):
        "Placeholder for overriding."
        pass

    def colliding(self):
        "Returns boolean answer to 'Is this agent colliding with anything?'"
        if self.colliding_wall():
            return True
        if self.colliding_tile():
            return True
        if self.colliding_sprites():
            return True
        return False

    def colliding_tile(self):
        "Returns boolean answer to 'Is this agent centered on a nowalk tile?'"
        if self.game.map.walkable_mask(self.sprite):
            return False
        return True

    def colliding_wall(self):
        "Returns boolean answer to 'Is this agent off the edge of its area?'"
        if self.area.contains(self.sprite.rect):
            return False
        return True

    def colliding_sprites(self):
        "Returns list of sprites this agent is currently colliding with."
        all_other_sprites = self.game.all_sprites.sprites()
        if self.sprite in all_other_sprites:
            # It might not be, if we're just testing a potential position
            all_other_sprites.remove(self.sprite)
        collision_test = pygame.sprite.collide_mask
        collided_sprites = [s for s in all_other_sprites if collision_test(self.sprite, s)]
        # This is what pygame.sprite.spritecollide is for, but it wasn't working for some reason.
        return collided_sprites

    def towards(self, target):
        "Returns direction this agent should turn to face the target Rect."
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
        "Wrapper for Character.stand(), which stops walk animation."
        self.sprite.stand()

    def turn(self, direction):
        "Wrapper for Character.turn(), which changes sprite orientation."
        self.sprite.turn(direction)

    def say(self, message, font = None):
        "Emit a message as a floating particle."
        if font is None:
            font = self.game.font
        offset = -1 * (self.sprite.rect.height/2 + font.get_height()/2 + 2)
        location = self.sprite.rect.move(0, offset)
        self.game.all_particles.add(particles.TextParticle(font, message, location))

    def interject(self, message, font = None):
        "Low-priority say(); discard if too frequent."
        if self.interject_ok:
            self.say(message, font)
            self.interject_ok = False
            timers.Timer(self.INTERJECT_TIMEOUT, self.reset_interject)

    def reset_interject(self):
        "Internal. Reset interjection timer."
        self.interject_ok = True

    def greet(self, font = None):
        "Interject a random greeting."
        while True:
            greeting = random.choice(self.texts["greetings"])
            if greeting not in self.last_greetings:
                self.last_greetings.pop(0)
                self.last_greetings.append(greeting)
                break
        self.interject(greeting, font)

    def place(self):
        px_x, px_y = self.sprite.rect.center
        if self.holding:
            return self.game.map.place(px_x, px_y, self.holding)
        return False

    def pick_up(self):
        px_x, px_y = self.sprite.rect.center
        item = self.game.map.pick_up(px_x, px_y)
        if item:
            self.holding = item
            return True
        return False


class Player(Agent):
    """
    A type of Agent (see its arguments) to be controlled by a player.
    Contains callables for game.Control and collision responses.
    """

    def colliding_wall(self):
        "If we're out of bounds, complain about the wall bump."
        if super(Player, self).colliding_wall():
            self.interject(random.choice(self.texts["ouches"]))
            return True
        return False

    def colliding_sprites(self):
        "If we hit a sprite, startle its agent."
        sprites = super(Player, self).colliding_sprites()
        if sprites:
            for sprite in sprites:
                if isinstance(sprite.agent, Npc):
                    if pygame.key.get_mods() & KMOD_CTRL:
                        sprite.agent.kill()
                    elif sprite.agent.is_startleable:
                        timers.Timer(100, sprite.agent.startled, self)
                        # this gives us time to finish the loop and uncollide
        return sprites

    def walk(self, direction, turn = None):
        if turn is None:
            if pygame.key.get_mods() & KMOD_SHIFT:
                self.turn(OPPOSITE[direction])
                turn = False
            else:
                turn = True
        super(Player, self).walk(direction, turn)

    def greet(self, font = None):
        "Greet nearby NPCs (triggered by a game.Control)"
        super(Player, self).greet(font)
        audible = pygame.sprite.collide_circle_ratio(2)
        earshot = [npc for npc in self.game.all_npcs if audible(self.sprite, npc.sprite)]
        for npc in earshot:
            npc.greeted()

    def call(self, font = None):
        "Call out to all NPCs (triggered by a game.Control)"
        if font is None:
            font = self.game.big_font
        self.interject(random.choice(self.texts["calls"]), font)
        for npc in self.game.all_npcs:
            npc.called(self)

    def place(self):
        if self.holding:
            result = super(Player, self).place()
            if result:
                self.interject("I placed {}.".format(self.holding.name))
            else:
                self.interject("I can't put {} here.".format(self.holding.name))
        else:
            self.interject("I'm not holding anything.")

    def pick_up(self):
        if super(Player, self).pick_up():
            self.interject("I picked up {}".format(self.holding.name))
        else:
            self.interject("I can't pick up anything here.")

    def inventory(self):
        if self.holding:
            self.interject("I'm carrying {}.".format(self.holding.name))
        else:
            self.interject("I'm not carrying anything.")


class Npc(Agent):
    """
    A type of Agent (see its arguments) which is computer-controlled.
    Wanders randomly and responds to collisions and player actions.
    """

    MIN_WANDER = 1500       # when NPC is wandering, how long before it stops
    MAX_WANDER = 6000
    MIN_STAND = 500         # when NPC is standing, how long before it
    MAX_STAND = 2000        # resumes wandering
    MIN_STARTWANDER = 800   # how long before a newly-spawned NPC
    MAX_STARTWANDER = 4000  # begins wandering
    MIN_GREETRESPONSE = 0   # how long before an NPC responds
    MAX_GREETRESPONSE = 500 # to being greeted
    MIN_PAUSE = 1000        # when NPC is called to, how long
    MAX_PAUSE = 4000        # will it stand and look
    SPEED = 1               # pixels per tick

    def __init__(self, *args):
        super(Npc, self).__init__(*args)
        if len(self.game.all_agents) < 8:
            in_use = [a.spriteno for a in self.game.all_agents]
            while self.spriteno in in_use:
                self.spriteno = None
                self.set_sprite()
        self.game.all_npcs.append(self)
        self.speed = self.SPEED
        self.direction = None
        self.is_startleable = True
        self.greet()
        self.timer = timers.Timer(random.randint(self.MIN_STARTWANDER, self.MAX_STARTWANDER), self.start_wandering)

    def update(self):
        "If we're currently wandering, step; if we hit something, turn around."
        if self.direction is not None:
            if not self.walk(self.direction):
                self.direction = OPPOSITE[self.direction]

    def kill(self):
        "Destroy sprite and remove self from groups."
        self.sprite.kill()
        self.game.all_agents.remove(self)
        self.game.all_npcs.remove(self)

    def colliding_sprites(self):
        "Excuse ourselves if we bump into a sprite."
        sprites = super(Npc, self).colliding_sprites()
        if sprites:
            self.interject(random.choice(self.texts["polite"]))
        return sprites

    def start_wandering(self):
        "Pick a random direction, walk for a while, then trigger stop."
        self.direction = random.choice([UP, DOWN, LEFT, RIGHT])
        self.timer = timers.Timer(random.randint(self.MIN_WANDER, self.MAX_WANDER), self.stop_wandering)

    def stop_wandering(self):
        "Stop, stand for a while, then trigger wandering."
        self.stand()
        self.direction = None
        self.timer = timers.Timer(random.randint(self.MIN_STAND, self.MAX_STAND), self.start_wandering)

    def greeted(self):
        "Respond to a greeting from the player."
        timers.Timer(random.randint(self.MIN_GREETRESPONSE, self.MAX_GREETRESPONSE), self.greet)

    def called(self, caller):
        "Respond to the player calling out."
        self.pause()
        self.turn(self.towards(caller.sprite.rect))

    def startled(self, startler):
        "Respond to the player bumping into us."
        self.is_startleable = False
        self.pause()
        facing = self.towards(startler.sprite.rect)
        self.turn(facing)
        self.walk(OPPOSITE[facing], False)
        timers.Timer(100, self.reset_startled)
        # no random here, because it's just to account for keyrepeat

    def reset_startled(self):
        "Internal. Reset the startle timer."
        self.stand()
        self.is_startleable = True

    def pause(self, duration = None):
        "Stop the wander cycle for a random time and optionally face a direction."
        if duration is None:
            duration = random.randint(self.MIN_PAUSE, self.MAX_PAUSE)
        self.direction = None
        self.stand()
        self.timer.cancel()
        self.timer = timers.Timer(duration, self.start_wandering)
