import random
import time
import displayio
import controls
import adafruit_imageload
import terminalio


def collide(ax0, ay0, ax1, ay1, bx0, by0, bx1=None, by1=None):
    if bx1 is None:
        bx1 = bx0
    if by1 is None:
        by1 = by0
    return not (ax1 < bx0 or ay1 < by0 or ax0 > bx1 or ay0 > by1)


class Sprite:
    def __init__(self, game, frame, x, y, width=1, height=1):
        self.grid = displayio.TileGrid(game.tiles,
            pixel_shader=game.palette, default_tile=frame,
            width=width, height=height, tile_width=16, tile_height=16)
        game.sprites.append(self.grid)
        self.x = x
        self.y = y
        self.game = game

    def move(self, x, y):
        self.grid.x = self.x = x
        self.grid.y = self.y = y

    def set_frame(self, frame, flip=False):
        if frame > 15:
            return
        self.grid[0, 0] = frame
        self.grid.flip_x = flip


class Ship(Sprite):
    def __init__(self, game):
        super().__init__(game, 3, 56, 102)
        self.dx = 0
        self.x = 56
        self.tick = 0
        self.dead = False

    def update(self):
        self.tick = not self.tick

        keys = controls.buttons.get_pressed()
        self.set_frame(3, 0 if self.tick else 4)
        if keys & controls.B_RIGHT:
            self.dx = min(self.dx + 1, 4)
            self.set_frame(4, 0)
        elif keys & controls.B_LEFT:
            self.dx = max(self.dx - 1, -4)
            self.set_frame(4, 4)
        else:
            self.dx = self.dx // 2
        if keys & controls.B_X:
            if self.game.missiles[0].grid.hidden:
                self.game.missiles[0].shoot(self.x, self.y)
            elif self.game.missiles[1].grid.hidden:
                self.game.missiles[1].shoot(self.x, self.y)
            elif self.game.missiles[2].grid.hidden:
                self.game.missiles[2].shoot(self.x, self.y)
        if keys & controls.B_O:
            self.game.pause(" Pause...")
        self.x = max(min(self.x + self.dx, 112), 0)
        self.move(self.x, self.y)


class Saucer(Sprite):
    def __init__(self, game):
        super().__init__(game, 9, 0, 0)
        self.tick = 0
        self.dx = 4
        self.move(0, 8)

    def update(self):
        self.tick = (self.tick + 1) % 6
        self.grid.flip_x = self.tick >= 3
        if self.x >= 128 or self.x <= -16:
            self.dx = -self.dx
        self.move(self.x + self.dx, self.y)
        if abs(self.x - self.game.ship.x) < 4 and self.game.bomb.grid.hidden:
            self.game.bomb.move(self.x, self.y)
            self.game.bomb.grid.hidden  = False


class Bomb(Sprite):
    def __init__(self, game):
        super().__init__(game, 5, 0, 128)
        self.boom = 0
        self.grid.hidden = True

    def update(self):
        if self.y >= 128:
            self.grid.hidden = True
        if self.grid.hidden:
            return
        if self.boom:
            if self.boom == 1:
                controls.audio.play(self.game.boom_sound)
            self.set_frame(12 + self.boom, 0)
            self.boom += 1
            if self.boom > 4:
                self.boom = 0
                self.game.ship.dead = True
                self.move(self.x, 128)
            return
        self.move(self.x, self.y + 8)
        self.set_frame(5, 0 if self.y % 16 else 4)
        ship = self.game.ship
        if collide(self.x + 4, self.y + 4, self.x + 12, self.y + 12,
                   ship.x + 4, ship.y + 4, ship.x + 12, ship.y + 12):
            self.boom = 1


class Missile(Sprite):
    def __init__(self, game, power):
        super().__init__(game, 12 - power, 0, -32)
        self.boom = 0
        self.power = power
        self.grid.hidden = True

    def update(self):
        if self.grid.hidden:
            return
        aliens = self.game.aliens
        if self.boom:
            if self.boom == 1:
                controls.audio.play(self.game.boom_sound)
            self.set_frame(13 + self.boom)
            self.boom += 1
            if self.boom > 4:
                self.boom = 0
                self.kill()
                aliens.grid[self.ax, self.ay] = 0
            return

        if self.y <= -32:
            self.kill()
            return
        self.move(self.x, self.y - 8)
        self.set_frame(12 - self.power, 0 if self.y % 16 == 6 else 4)
        self.ax = (self.x + 8 - aliens.x) // 16
        self.ay = (self.y + 4 - aliens.y) // 16
        if 0 <= self.ax <= 6 and 0 <= self.ay <= 2:
            if (self.x + 10 - aliens.x) % 16 > 4 and aliens.grid[self.ax, self.ay]:
                aliens.grid[self.ax, self.ay] = 6
                self.move(self.x, self.y - 4)
                self.boom = 1
                aliens.dirty = True

    def shoot(self, x, y):
        controls.audio.play(self.game.pew_sound)
        self.move (x, y)
        self.grid.hidden = False

    def kill(self):
        self.set_frame(12 - self.power)
        self.grid.hidden = True


class Aliens(Sprite):
    def __init__(self, game):
        super().__init__(game, 7, 8, 17, 7, 3)
        self.tick = self.left = self.right = self.descend = 0
        self.dx = 2
        self.dirty = False
        self.reform()

    def update(self):
        self.tick = (self.tick + 1) % 4
        if self.tick in (0, 2):
            for x in range(7):
                for y in range(3):
                    if self.grid[x, y] == 7:
                        self.grid[x, y] = 8
                    elif self.grid[x, y] == 8:
                        self.grid[x, y] = 7
            if self.x >= 14 + self.right or self.x <= 2 - self.left:
                self.y += 1
                self.descend += 1
                if self.descend >= 4:
                    self.descend = 0
                    self.dx = -self.dx
                    self.x += self.dx
            else:
                self.x += self.dx
            self.move(self.x, self.y)

    def reform(self):
        self.left = 16 * 6
        self.right = 16 * 6
        for y in range(3):
            for x in range(7):
                if self.grid[x, y] in (7, 8):
                    self.left = min(16 * x, self.left)
                    self.right = min(96 - 16 * x, self.right)
        self.dirty = False


class Game:
    def __init__(self):
        self.tiles, self.palette = adafruit_imageload.load("tiles.gif",
            bitmap=displayio.Bitmap, palette=displayio.Palette)
        self.palette.make_transparent(15)
        self.pew_sound = open("pew.wav", 'rb')
        self.boom_sound = open("boom.wav", 'rb')

        self.root = displayio.Group(max_size=3)
        self.sprites = displayio.Group(max_size=8)
        space_palette = displayio.Palette(16)
        for i in range(16):
            space_palette[i] = self.palette[i]
        space_palette[15] = space_palette[0]
        self.space = displayio.TileGrid(self.tiles, pixel_shader=space_palette,
            width=16, height=16, tile_width=16, tile_height=16, default_tile=0)
        for i in range(8):
            self.space[random.randint(0, 7),
                       random.randint(0, 7)] = random.randint(1, 2)
        self.ship = Ship(self)
        self.aliens = Aliens(self)
        self.saucer = Saucer(self)
        self.bomb = Bomb(self)
        self.missiles = [Missile(self, 0), Missile(self, 1), Missile(self, 2)]
        self.mobs = [self.ship, self.aliens, self.saucer, self.bomb] + self.missiles
        self.root.append(self.space)
        self.root.append(self.sprites)

        w, h = terminalio.FONT.get_bounding_box()
        text_palette = displayio.Palette(2)
        text_palette[0] = 0x000000
        text_palette[1] = 0xFFFFFF
        text_palette.make_transparent(0)
        text_grid = displayio.TileGrid(terminalio.FONT.bitmap,
            pixel_shader=text_palette,
            tile_width=w, tile_height=h, width=9, height=1)
        text_grid.x = (controls.display.width - 9 * w) // 2
        text_grid.y = (controls.display.height -  h) // 2
        self.text = terminalio.Terminal(text_grid, terminalio.FONT)
        self.root.append(text_grid)

        self.last_tick = time.monotonic()

        controls.display.show(self.root)
        controls.audio.mute(False)


    def pause(self, info):
        while controls.buttons.get_pressed() & controls.B_O:
            pass
        self.text.write('\n')
        self.text.write(info)
        while not controls.buttons.get_pressed() & controls.B_O:
            pass
        self.text.write('\n')
        self.text.write(' ' * 9)
        while controls.buttons.get_pressed() & controls.B_O:
            pass

    def tick(self, fps=12):
        self.last_tick += 1 / fps
        wait = max(0, self.last_tick - time.monotonic())
        if wait:
            time.sleep(wait)
        else:
            self.last_tick = time.monotonic()


    def run(self):
        while (self.aliens.left + self.aliens.right < 112 and
               self.aliens.y < 80 and not self.ship.dead):
            for mob in self.mobs:
                mob.update()
            if self.aliens.dirty:
                self.aliens.reform()
            self.tick()

        if self.ship.dead or self.aliens.y >= 80:
            self.pause("Game Over")
        else:
            self.pause("You won!")

while True:
    Game().run()
