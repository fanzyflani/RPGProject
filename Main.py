#!/usr/bin/env python2 --
'''RPG based off of the PortalDAGger engine written by Ben Russell and Tom Goodman'''

try:
    import time
    import constants
    import sys
    import random
    import math
    import os
    import getopt
    import pygame
    import Levels
    from socket import *
    from pygame.locals import *
except ImportError, err:
    print "couldn't load module. %s" % (err)
    sys.exit(2)

pygame.init()
'''music = pygame.mixer.music.load(constants.MUSIC_FILEPATH)'''

VERSION = constants.VERSION

WIDTH = constants.WIDTH
HEIGHT = constants.HEIGHT
SCALE = constants.SCALE

FPS = constants.FPS
SPF = 1.0/FPS
CAMBORDER = constants.CAMBORDER

real_camx = WIDTH//2
real_camy = HEIGHT//2

'''Set up the display'''
pygame.display.set_caption(constants.GAME_TITLE)
screen_real = pygame.display.set_mode((WIDTH*SCALE, HEIGHT*SCALE), 0, 0)
screen = pygame.Surface((WIDTH,HEIGHT), 0, screen_real.get_bitsize()).convert(screen_real)

def subtile(img, w, h, cx, cy):
    '''
    Gets a tile-indexed w by h subsurface from the tilemap "img".
    '''

    return img.subsurface((cx*w, cy*h, w, h))

'''Load the tile images. These will be stored in a tga format'''
img_tiles = pygame.image.load(os.path.join("dat", constants.TILES_FILEPATH))
img_tiles = img_tiles.convert(screen)


img_tiles_grass_light = subtile(img_tiles, 16, 16, 0, 1)
img_tiles_path_sandy = subtile(img_tiles, 16, 16, 0, 2)
img_tiles_wall_stone = subtile(img_tiles, 16, 16, 0, 3)
img_tiles_doorno = subtile(img_tiles, 16, 16, 0, 4)
img_tiles_stone_sketchy = subtile(img_tiles, 16, 16, 0, 5)
img_tiles_water_light = subtile(img_tiles, 16, 16, 0, 6)
img_tiles_portal_red = subtile(img_tiles, 16, 16, 0, 7)


'''The above are the old images. Different images will be used depending on the
game'''

def rgb(r, g, b):
    '''
    Turns an RGB tuple into a colour value.
    '''

    return screen.map_rgb((r, g, b))

def flip_screen():
    '''
    Push the back buffer to the front buffer.
    i.e., actually draw what you were drawing
    to the screen.
    '''

    pygame.transform.scale(screen,
                           (screen_real.get_width(), screen_real.get_height()),
                           screen_real)
    pygame.display.flip()

class BaseCell:
    colour = rgb(255, 0, 255)
    imgs = None
    solid = True

    def draw(self, surf, x, y, world):
        '''
        Draws the cell to the surface, "surf".
        '''
        if self.imgs == None:
            '''No Image'''
            pass
        elif type(self.imgs) in (list, tuple,):
            '''
            Indexable sequence - pick an image
            '''
            surf.blit(self.imgs[0], (x, y))
            #TODO: do more than just the first image
        else:
            '''
            Assuming this is a single image
            '''
            surf.blit(self.imgs, (x, y))

    def on_enter(self, ent):
        '''
        CALBACK: Handles entry of an entity.
        '''
        pass

    def on_exit(self, ent):
                """
                CALLBACK: Handles exit of an entity.
                """
                pass

    def is_solid(self, world=None):
                """
                Determines if this cell is solid or not.
                """
                return self.solid

class BaseEnt:
    colour = rgb(255, 0, 255)
    rect = (4, 4, 8, 8)
    world = 0

    def __init__(self, lvl, cx, cy):
        '''
        Places an entity on level, "lvl", at cell cx, cy.
        '''
        self.lvl = lvl
        self.cx, self.cy = cx, cy
        self.ox, self.oy = 0, 0

    def draw(self, surf, x, y, world):
        '''
        Draws the entity at pixel position x, y.
        '''
        rx, ry, rw, rh = self.rect
        rx += x + self.cx*16 + self.ox
        ry += y + self.cy*16 + self.oy
        pygame.draw.rect(surf, self.colour, (rx, ry, rw, rh))

    def tick(self):
        '''
        Logic Update for entity.
        TO BE OVERRIDED BY SUBCLASSES.
        '''

        pass

class PlayerEnt(BaseEnt):
    colour = rgb(0, 255, 255)

    def cell_is_walkable(self, cx, cy, world=None):
        '''
        Determine if we can walk onto a given cell.
        '''

        # Get the relevant "world" we're checking this for.
        if world == None:
            world = self.world

        # Get cell
        cell = self.lvl.get_cell(cx, cy)

        # Check if None
        if cell == None:
            return False # NEVER WALKABLE!

        # Check if Solid
        return not cell.is_solid(world=world)

    def tick(self):
        '''
        Used to update the Player Entity
        '''
        #Move to relevant cell if need be
        if not(self.ox == 0 and self.oy == 0):
            if self.ox != 0:
                self.ox += (1 if self.ox < 0 else -1)
            if self.oy != 0:
                self.oy += (1 if self.oy < 0 else -1)

            # If we've just entered the cell, call on_enter
            if self.ox == 0 and self.oy == 0:
                self.lvl.get_cell(self.cx, self.cy).on_enter(self)

       #Set camera
        rx = self.cx*16 + self.ox + 8
        ry = self.cy*16 + self.oy + 8

        global real_camx
        global real_camy
        if rx - real_camx < -(WIDTH//2 - CAMBORDER):
                real_camx = (WIDTH//2 - CAMBORDER) + rx
        if rx - real_camx > (WIDTH//2 - CAMBORDER):
                real_camx = -(WIDTH//2 - CAMBORDER) + rx
        if ry - real_camy < -(HEIGHT//2 - CAMBORDER):
                real_camy = (HEIGHT//2 - CAMBORDER) + ry
        if ry - real_camy > (HEIGHT//2 - CAMBORDER):
                real_camy = -(HEIGHT//2 - CAMBORDER) + ry

        if self.ox == 0 and self.oy == 0:
                # Work out movement
                vx, vy = 0, 0
                if newkeys[pygame.K_LEFT]:
                        vx -= 1
                if newkeys[pygame.K_RIGHT]:
                        vx += 1
                if newkeys[pygame.K_UP]:
                        vy -= 1
                if newkeys[pygame.K_DOWN]:
                        vy += 1

                # Bail if we're not moving anywhere
                if vx == 0 and vy == 0:
                        return

                # Work out if anything is in that cell
                if self.cell_is_walkable(self.cx + vx, self.cy + vy):
                        self.lvl.get_cell(self.cx, self.cy).on_exit(self)
                        self.cx += vx
                        self.cy += vy
                        self.ox -= 16*vx
                        self.oy -= 16*vy
                elif self.cell_is_walkable(self.cx + vx, self.cy):
                        self.lvl.get_cell(self.cx, self.cy).on_exit(self)
                        self.cx += vx
                        self.ox -= 16*vx
                elif self.cell_is_walkable(self.cx, self.cy + vy):
                        self.lvl.get_cell(self.cx, self.cy).on_exit(self)
                        self.cy += vy
                        self.oy -= 16*vy

class GrassCellLight(BaseCell):
    colour = rgb(170, 100, 85)
    imgs = img_tiles_grass_light
    solid = False

class PathCellSandy(BaseCell):
    colour = rgb(170, 100, 85)
    imgs = img_tiles_path_sandy
    solid = False

class WallCellStone(BaseCell):
    colour = rgb(55, 55, 55)
    imgs = img_tiles_wall_stone 
    solid = True

class StoneCellSketchy(BaseCell):
    colour = rgb(55, 55, 55)
    imgs = img_tiles_stone_sketchy
    solid = False

class WaterCellLight(BaseCell):
    colour = rgb(0, 0, 170)
    imgs = img_tiles_water_light
    solid = True # To prevent walking on it...

class Level:
    """
    A Level contains all the logic and stuff for a, well, level.
    """
    def __init__(self, data):
        # Allocate entity list
        self.ents = []
        self.player = None
        self.player_spawn = None

        # Allocate grid
        self.g = [[None for x in xrange(len(data[0]))]
                for y in xrange(len(data))]

        # Put stuff into grid
        for l, y in zip(data, xrange(len(data))):
                for c, x in zip(l, xrange(len(l))):
                        self.g[y][x] = self.translate_level_char(c, x, y)

    def respawn_player(self):
        self.player.cx, self.player.cy = self.player_spawn
        self.player.ox, self.player.oy = (0, 0)
        global real_camx
        global real_camy
        real_camx, real_camy = map(lambda v: v*16+8, self.player_spawn)

    def get_cell(self, x, y):
        """
        Gets a cell from the level for inspection or mutilation.
        """
        if y < 0 or y >= len(self.g): return None
        if x < 0 or x >= len(self.g[y]): return None
        return self.g[y][x]

    def tick(self):
        """
        Logic update for level.
        """
        # Update entities
        for ent in self.ents:
                ent.tick()

    def draw(self, surf, camx, camy, world):
        """
        Draws the level at (-camx, -camy) on surface "surf", using world "world".
        """

        # Draw cells
        for y in xrange(len(self.g)):
            for x in xrange(len(self.g[0])):
              cell = self.g[y][x]
              if cell != None:
                  cell.draw(surf, x*16-camx, y*16-camy, world)

        # Draw entities
        for ent in self.ents:
            ent.draw(surf, -camx, -camy, world)

    def translate_level_char(self, c, x, y):
        """
        Maps a character from the source level to an actual class.
        """

        if c == ".":
            return None

        elif c == ",":
            return GrassCellLight()

        elif c == "p":
            return PathCellSandy()

        elif c == "#":
            return WallCellStone()

        elif c == "s":
            return StoneCellSketchy()

        elif c == "w":
            return WaterCellLight()

        elif c == "@":
            assert self.player == None
            self.player_spawn = (x, y)
            self.player = PlayerEnt(self, x, y)
            self.ents.append(self.player)
            return GrassCellLight()

        else:
            raise Exception("invalid level char: %s" % repr(c))  

LVL_STRINGS = Levels.LVL_STRINGS

#One list to rule them all
levelList = map(Level, LVL_STRINGS)

#Used to determine what level the player is on
levelPos = 0

# Main loop
quitflag = False
oldkeys = pygame.key.get_pressed()

newkeys = pygame.key.get_pressed()
tick_next = time.time()
#pygame.mixer.music.play(-1)
while not quitflag:
        # Handle timing
        tick_current = time.time()

        if tick_current < tick_next:
                # Draw screen
                screen.fill(rgb(0,0,170))
                levelList[levelPos].draw(screen,
                    real_camx - WIDTH//2,
                    real_camy - HEIGHT//2,
                    levelList[levelPos].player.world)
                flip_screen()

                # Prevent CPU fires
                time.sleep(0.01)

        else:
                # Poll events
                pygame.event.pump()
                newkeys = pygame.key.get_pressed()
                if oldkeys[pygame.K_ESCAPE] and not newkeys[pygame.K_ESCAPE]:
                    quitflag = True

                # Update logic
                levelList[levelPos].tick()

                # Transfer newkeys to oldkeys
                oldkeys = newkeys

                # Update tick counter
                tick_next += SPF


# Clean up
pygame.quit()


