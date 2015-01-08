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
img_tiles_lava = subtile(img_tiles, 16, 16, 0, 4)
img_tiles_mountain_floor = subtile(img_tiles, 16, 16, 0, 5)
img_tiles_water_light = subtile(img_tiles, 16, 16, 0, 6)
img_tiles_snow = subtile(img_tiles, 16, 16, 0, 7)
img_tiles_grass_long = subtile(img_tiles, 16, 16, 0, 8)
img_tiles_path_stone = subtile(img_tiles, 16, 16, 0, 9)
img_tiles_grass_flowers = subtile(img_tiles, 16, 16, 0, 10)
img_tiles_sand = subtile(img_tiles, 16, 16, 0, 11)
img_tiles_volcanic_floor = subtile(img_tiles, 16, 16, 0, 12)
img_tiles_stone_floor = subtile(img_tiles, 16, 16, 0, 13)
img_tiles_boulder = subtile(img_tiles, 16, 16, 0, 14)

img_player_sprites = pygame.image.load(os.path.join("dat", "Spritesheet.gif"))
img_player_sprites = img_player_sprites.convert(screen)

img_player_sprites_down_right = subtile(img_player_sprites, 16, 16, 0, 0)
img_player_sprites_down_standing = subtile(img_player_sprites, 16, 16, 1, 0)
img_player_sprites_down_left = subtile(img_player_sprites, 16, 16, 2, 0)
img_player_sprites_left_right = subtile(img_player_sprites, 16, 16, 0, 1)
img_player_sprites_left_standing = subtile(img_player_sprites, 16, 16, 1, 1)
img_player_sprites_left_left = subtile(img_player_sprites, 16, 16, 2, 1)
img_player_sprites_right_right = subtile(img_player_sprites, 16, 16, 0, 2)
img_player_sprites_right_standing = subtile(img_player_sprites, 16, 16, 1, 2)
img_player_sprites_right_left = subtile(img_player_sprites, 16, 16, 2, 2)
img_player_sprites_up_right = subtile(img_player_sprites, 16, 16, 0, 3)
img_player_sprites_up_standing = subtile(img_player_sprites, 16, 16, 1, 3)
img_player_sprites_up_left = subtile(img_player_sprites, 16, 16, 2, 3)

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

class BaseEnt():
    colour = rgb(255, 0, 255)
    rect = (4, 4, 8, 8)
    world = 0

    def __init__(self, lvl, cx, cy, sprite):
        '''
        Places an entity on level, "lvl", at cell cx, cy.
        '''
        self.lvl = lvl
        self.cx, self.cy = cx, cy
        self.ox, self.oy = 0, 0
        self.sprite = sprite

    def draw(self, surf, x, y, world):
        '''
        Draws the entity at pixel position x, y.
        '''
        if self.sprite == None:
            rx, ry, rw, rh = self.rect
            rx += x + self.cx*16 + self.ox
            ry += y + self.cy*16 + self.oy
            pygame.draw.rect(surf, self.colour, (rx, ry, rw, rh))
        else:
            rx, ry, rw, rh = self.rect
            rx += x + self.cx*16 + self.ox - 4
            ry += y + self.cy*16 + self.oy - 4
            surf.blit(self.sprite, (rx, ry, rw, rh))
    def tick(self):
        '''
        Logic Update for entity.
        TO BE OVERRIDED BY SUBCLASSES.
        '''

        pass

class PlayerEnt(BaseEnt):
    colour = rgb(0, 255, 255)
    stepcount = 0
    spr_chain = None

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

            # Advance sprite
            self.stepcount += 1
            self.stepcount %= 32
            if self.spr_chain:
                self.sprite = self.spr_chain[self.stepcount//8]

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
                k_left = newkeys[pygame.K_LEFT] or newkeys[pygame.K_a]
                k_right = newkeys[pygame.K_RIGHT] or newkeys[pygame.K_d]
                k_up = newkeys[pygame.K_UP] or newkeys[pygame.K_w]
                k_down = newkeys[pygame.K_DOWN] or newkeys[pygame.K_s]

                if k_left:
                        vx -= 1
                        self.spr_chain = [
                            img_player_sprites_left_standing,
                            img_player_sprites_left_left,
                            img_player_sprites_left_standing,
                            img_player_sprites_left_right,
                        ]

                if k_right:
                        vx += 1
                        self.spr_chain = [
                            img_player_sprites_right_standing,
                            img_player_sprites_right_left,
                            img_player_sprites_right_standing,
                            img_player_sprites_right_right,
                        ]

                if k_up:
                        vy -= 1
                        self.spr_chain = [
                            img_player_sprites_up_standing,
                            img_player_sprites_up_left,
                            img_player_sprites_up_standing,
                            img_player_sprites_up_right,
                        ]

                if k_down:
                        vy += 1
                        self.spr_chain = [
                            img_player_sprites_down_standing,
                            img_player_sprites_down_left,
                            img_player_sprites_down_standing,
                            img_player_sprites_down_right,
                        ]

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

class FloorCell(BaseCell):
    '''All Floor Cells aren't Solid'''
    colour = (55, 55, 55)
    solid = False

class WallCell(BaseCell):
    '''All Wall Cells are Solid'''
    colour = (55, 55, 55)
    solid = True
    
class GrassCellLight(FloorCell):
    imgs = img_tiles_grass_light

class PathCellSandy(FloorCell):
    imgs = img_tiles_path_sandy

class WallCellStone(WallCell):
    imgs = img_tiles_wall_stone 

class LavaCell(WallCell):
    imgs = img_tiles_lava

class MountainCellFloor(FloorCell):
    imgs = img_tiles_mountain_floor

class WaterCellLight(WallCell):
    imgs = img_tiles_water_light

class SnowCell(FloorCell):
    imgs = img_tiles_snow

class GrassCellLong(FloorCell):
    imgs = img_tiles_grass_long

class PathCellStone(FloorCell):
    imgs = img_tiles_path_stone

class GrassCellFlowers(FloorCell):
    imgs = img_tiles_grass_flowers

class SandCell(FloorCell):
    imgs = img_tiles_sand

class VolcanicCellFloor(FloorCell):
    imgs = img_tiles_volcanic_floor

class StoneCellFloor(FloorCell):
    imgs = img_tiles_stone_floor

class BoulderCell(WallCell):
    imgs = img_tiles_boulder

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
        
        elif c == "l":
            return LavaCell()
        
        elif c == "-":
            return MountainCellFloor()

        elif c == "w":
            return WaterCellLight()

        elif c == "s":
            return SnowCell()

        elif c == "<":
            return GrassCellLong()

        elif c == "P":
            return PathCellStone()

        elif c == ">":
            return GrassCellFlowers()

        elif c == "*":
            return SandCell()

        elif c == "v":
            return VolcanicCellFloor()

        elif c == "_":
            return StoneCellFloor()

        elif c == "b":
            return BoulderCell()

        elif c == "@":
            assert self.player == None
            self.player_spawn = (x, y)
            self.player = PlayerEnt(self, x, y, img_player_sprites_down_standing)
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


