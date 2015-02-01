import collections
import curses
import math
import numpy as np
import os
import random
import time
from pykeyboard import PyKeyboardEvent

def get_winsize():
    rows, columns = os.popen('stty size', 'r').read().split()
    return int(rows), int(columns)

KEY_LEFT  = 113
KEY_RIGHT = 114
KEY_UP    = 111
KEY_DOWN  = 116
KEY_SPACE = 65

FRAME_RATE = 45 # fps
LEVEL_WIDTH = 130
LEVEL_HEIGHT = 35

# Whether or not each key is pressed
pressed = { KEY_LEFT  : False,
            KEY_RIGHT : False,
            KEY_UP    : False,
            KEY_DOWN  : False,
            KEY_SPACE : False }

# Load the high score
HIGH_SCORE = 0
try:
    HIGH_SCORE = int(open('.HIGH_SCORE', 'r').readlines()[0].strip())
except:
    pass


class Listener(PyKeyboardEvent):
    def tap(self, keycode, character, press):
        pressed[keycode] = press

class Copter:
    def __init__(self):

        # Initial copter location
        self.x = 20
        self.y = LEVEL_HEIGHT/2

        #   ___.___
        # *===[_)
        #     ---
        self.body = [
            # Top
            ('_', (-3,  1)),
            ('_', (-2,  1)),
            ('_', (-1,  1)),
            ('.', ( 0,  1)),
            ('_', ( 1,  1)),
            ('_', ( 2,  1)),
            ('_', ( 3,  1)),
            # Middle
            ('*', (-5,  0)),
            ('=', (-4,  0)),
            ('=', (-3,  0)),
            ('=', (-2,  0)),
            ('[', (-1,  0)),
            ('_', ( 0,  0)),
            (')', ( 1,  0)),
            # Bottom
            ('-', (-1, -1)),
            ('-', ( 0, -1)),
            ('-', ( 1, -1)),
        ]
        
        # Current velocity and acceleration
        self.dy = 0
        self.ddy = 0
    
        # Max velocity and acceleration
        self.max_vel = .8
        self.max_acc = .05

        # Other properties
        self.smoke = collections.deque()
        self.crashed = False

class Level:
    def __init__(self):
        self.blocks = collections.deque()
        self.distance = 0
        for x in xrange(LEVEL_WIDTH+1):
            self.blocks.append([(0, '#'), (LEVEL_HEIGHT+1, '#')])
        self.fromTop = 0

def main(arg):

    # Initialize curses
    screen = curses.initscr()
    screen.nodelay(1)
    curses.curs_set(0)
    curses.use_default_colors() #42ff23

    # Create the window
    rows, columns = get_winsize()
    win = curses.newwin(rows, columns, 0, 0)
    horizontal_border = (columns - LEVEL_WIDTH) / 2
    vertical_border = (rows - LEVEL_HEIGHT) / 2
    win.refresh()

    p = Copter()
    v = Level()

    def put(win, x, y, char):
        if not 0 <= x <= LEVEL_WIDTH+1:
            exit(1)
        if not 0 <= y <= LEVEL_HEIGHT+1:
            exit(1)
        win.addstr(rows-vertical_border-y, horizontal_border+x, char)

    def step():

        # Determine the location of the player
        if pressed[KEY_SPACE]:
            p.ddy = p.max_acc
        else:
            p.ddy = -1*p.max_acc
        p.dy += p.ddy
        if (abs(p.dy) > p.max_vel):
            if (p.dy < 0):
                p.dy = -1*p.max_vel
            else:
                p.dy = p.max_vel
        p.y += p.dy
        p.smoke.append(int(round(p.y)))
        if len(p.smoke) > p.x-5:
            p.smoke.popleft()

        # Generate the next column
        v.blocks.popleft()
        col = []

        # grow the walls
        wallSize = int(math.sqrt(v.distance/10))
        if random.random() > 0.5: # Grow down
            if (v.fromTop > 0) and random.random() < 0.1: # 0.1 chance of changing
                v.fromTop -= 1
        else: # Grow up
            if (v.fromTop  < wallSize) and random.random() < 0.1: # 0.1 chance of changing
                v.fromTop += 1
        col.append((LEVEL_HEIGHT-v.fromTop, '#'))
        col.append((wallSize-v.fromTop, '#'))

        # sprinkle random chars
        for i in xrange(wallSize-v.fromTop, LEVEL_HEIGHT-v.fromTop):
            if random.random()*2.5 < .001 + v.distance/500000.:
                col.append((i, '#'))
                    
        # Append the new column
        v.blocks.append(col)

        # Check for a collision, where center of the copter is used as reference
        #   ___.___
        # *===[_)
        #     0 o
        for char,(x,y) in p.body:
            if (int(round(p.y + y))) in [x for x,c in v.blocks[p.x + x]]:
                p.crashed = True

        # Increment the distance
        v.distance += 1 

        # Update the high score
        global HIGH_SCORE
        if v.distance > HIGH_SCORE:
            HIGH_SCORE = v.distance

        # If we've crashed, write the high score
        if p.crashed:
            try:
                out = open('.HIGH_SCORE', 'w')
                out.write(str(HIGH_SCORE) + '\n')
                out.close()
            except:
                pass

    def draw():
        win.clear()
        for char,(x,y) in p.body:
            put(win, p.x+x, int(round(p.y))+y, char)
        for i,y in enumerate(p.smoke):
            put(win, p.x-5-(len(p.smoke)-i), int(round(y)), '.')
        for x, ys in enumerate(v.blocks):
            for y,char in ys:
                put(win, x, y, char)
        score = '| Score: ' + str(v.distance)
        high = '   High Score: ' + str(HIGH_SCORE) + ' |'
        put(win, 47, 2, score)
        put(win, 47 + len(score), 2, high)
        put(win, 47, 3, '-'*(len(score)+len(high)))
        put(win, 47, 1, '-'*(len(score)+len(high)))
        win.refresh()
        curses.flushinp()

    # Loop forever
    while True:
        start = time.time()
        if not p.crashed:
            step() # Step forward the state of the game
        else:
            if pressed[KEY_SPACE]:
                break
        draw() # Draw the state of the game
        curses.napms(int(1000*(1./FRAME_RATE - (time.time()-start))))

# Initialize a keyboard listener
k = Listener()
k.start()

# Ensure curses is cleaned up correctly
while True:
    curses.wrapper(main)
