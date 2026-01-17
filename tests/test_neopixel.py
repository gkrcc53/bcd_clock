# simple neopixel test
# turn led 0..2 on in red, green, blue
# Fixed brightness factor of 0.2
# 16x16 panel in white draws nearly 1.5A

import sys
import time
from machine import Pin
import genlib as gl
from neopixel import NeoPixel

print()

cfg = gl.get_board_config()
hcfg = gl.get_config('hw.cfg')
cfg = cfg | hcfg
dcfg = gl.get_config('display.cfg')
cfg |= dcfg
keys = cfg.keys()
debug = 'debug' in cfg and cfg['debug']
verbose = False
if debug:
    verbose = 'verbose' in cfg and cfg['verbose']
    for key in sorted(keys):
        print(f'{key:25}{cfg[key]}')
    print()

# Initialize hardware
if 'neopixel_din' not in keys:
    print('NeoPixel DIN pin not configured')
    sys.exit(1)

din = cfg['neopixel_din']
cols = cfg['neopixel_cols']
rows = cfg['neopixel_rows']
orient = cfg['neopixel_orientation']
cnt = cols * rows
neo = NeoPixel(Pin(din), cols * rows)

# Convert a led array position to a linear 2D coordinate position
# for upper right alternating orientation.
# array[0] is at upper right corner of the led array
# array[cols] is at the left side of the second row
def _ura2xy(pos, cols, rows):
    row = pos // cols
    if row & 1:
        return pos
    else:
        pos %= cols
        return row * cols + cols - 1 - pos

# Convert a led array position to a linear 2D coordinate position
# for upper left normal orientation.
# array[0] is at upper left corner of the led array
# array[cols] is at the left side of the second row.
# This is the default 2D coordinate system
def _uln2xy(pos, cols, rows):
    return pos

ORIENTATION_UPPER_LEFT_NORM = 0
ORIENTATION_UPPER_RIGHT_ALT = 5

_lin2xy = _ura2xy if orient == ORIENTATION_UPPER_RIGHT_ALT else _uln2xy

# Set the color of a pixel at given led array position
def pixel1d(i, color):
    neo[i] = (int(color[0]*0.2), int(color[1]*0.2), int(color[2]*0.2))

# Set the color of a pixel at given 2D array position
def pixel2d(x, y, color):
    pos = _lin2xy(x + y * cols, cols, rows)
    if (pos > -1) and (pos < cnt):
        pixel1d(pos, color)

# Fill with white to check current drain
def test0():
    print('All white')
    neo.fill((51, 51, 51))
    show()
    time.sleep(5)
    clear()

def show():
    neo.write()

def clear(update=True):
    neo.fill((0,0,0))
    if update:
        show()

# check if color correct
def test1():
    global cnt
    print('1D pixels --> [0] = red, [1] = green, [2] = blue')
    pixel1d(0, (0x10, 0, 0))
    if cnt > 1:
        pixel1d(1, (0, 0x10, 0))
    if cnt > 2:
        pixel1d(2, (0, 0, 0x10))
    show()

# check if row/column order correct
def test2():
    clear()
    time.sleep(2)
    print('2D pixels --> [0,0] = red, [1,0] = green, [2,0] = blue, [max,max] = yellow')
    pixel2d(0, 0, (0x20,0,0))
    pixel2d(1, 0, (0x0,0x20,0))
    pixel2d(2, 0, (0x0,0,0x20))
    pixel2d(cols-1, rows-1, (0x20, 0x20, 0))
    show()

def test3():
    global cnt
    print('2D pixels --> [0,0] white, if [8,0]==[0,1] white, if [16,0]==[0,1] white')
    pixel2d(0, 0, (0x20, 0x20, 0x20))
    if cnt > 8:
        pixel2d(8, 0, (0x20, 0x0, 0x0))
        pixel2d(0, 1, (0x20, 0x20, 0x20))
    if cnt > 16:
        pixel2d(16, 0, (0x20, 0x0, 0x0))
        pixel2d(0, 1, (0x20, 0x20, 0x20))
    show()

def test4():
    print('1D walk')
    for pos in range(cnt):
        pixel1d(pos, (0x20, 0x20, 0))
        show()
        pixel1d(pos, (0, 0, 0))
        show()

    print('2D walk')
    for y in range(rows):
        for x in range(cols):
            pixel2d(x, y, (0, 0x20, 0x20))
            show()
            pixel2d(x, y, (0, 0, 0))
            show()
    
if __name__ == "__main__":
    test0()
    test1()
    time.sleep(5)
    test2()
    time.sleep(5)
    test3()
    time.sleep(5)
    test4()
    clear()
    show()
