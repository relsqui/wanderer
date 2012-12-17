import random, pygame
from modules.constants import *
from modules import particles, timers, sprites

class Agent(object):
    """
    Data relating to an agent (PC/NPC). Arguments:
        screen          (pygame.Surface inside which the agent can move)
        font            (pygame.font.Font for use in speaking)
        all_particles   (list of all particles)
        all_sprites     (list of all sprites)
        sprite          (optional: which # sprite to use, defaults to random)
        location        (optional: (x, y) location to center sprite on)
        name            (optional: string to call this agent)
    """

    def __init__(self, screen, font, all_particles, all_sprites, sprite = None, location = None, name = "Anonymous Agent"):
        super(Agent, self).__init__()
        self.all_particles = all_particles
        self.all_sprites = all_sprites
        self.name = name
        self.speed = PLAYER_SPEED

        self.font = font
        self.last_greetings = [None for x in xrange(5)]
        self.interject_ok = True

        self.area = screen.get_rect()
        if not sprite:
            sprite = random.randrange(1, 8)
        self.set_sprite(sprite, location)

    def __repr__(self):
        return self.name

    def set_sprite(self, spriteno, location = None):
        spriteno -= 1
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
            self.sprite.kill()
        elif not location:
            while True:
                locx = random.randrange(0, self.area.width - SPRITE_WIDTH)
                locy = random.randrange(0, self.area.height - SPRITE_HEIGHT)
                location = pygame.Rect(locx, locy, SPRITE_WIDTH, SPRITE_HEIGHT)
                self.sprite = sprites.Character(char_sheet, location, self)
                if not self.colliding():
                    break
                else:
                    self.sprite.kill()
        self.all_sprites.add(self.sprite)

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
        all_other_sprites = self.all_sprites.sprites()
        if self.sprite in all_other_sprites:
            # It might not be, if we're just testing a potential position
            all_other_sprites.remove(self.sprite)
        collision_test = pygame.sprite.collide_mask
        collided_sprites = [s for s in all_other_sprites if collision_test(self.sprite, s)]
        # This is what pygame.sprite.spritecollide is for, but it wasn't working for some reason.
        if collided_sprites:
            for sprite in collided_sprites:
                sprite.agent.interject(random.choice(GREETINGS))
            return collided_sprites
        return False

    def move(self, direction):
        "Try to move in a direction."
        self.sprite.walk(direction)
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

    def stop(self):
        self.sprite.stand()

    def say(self, message):
        "Emit a message as a floating particle."
        offset = -1 * (self.sprite.rect.height/2 + FONT_SIZE/2 + 2)
        destination = self.sprite.rect.move(0, offset)
        self.all_particles.add(particles.TextParticle(self.font, message, destination))

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
