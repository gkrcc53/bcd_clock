# simple neopixel test
# turn led 0..2 on in red, green, blue
# Fixed brightness factor of 0.2
# 16x16 panel in white draws more than 2A

# Make sure we're on the right platform
import sys
import genlib as gl
if gl.platform == 'linux':
    print('This program/module was not written for this platform')
    sys.exit(1)

import time
from machine import Pin
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
order = cfg['neopixel_pixel_order']
delay = 10
if 'neopixel_show_delay' in cfg:
    delay = cfg['neopixel_show_delay']
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


ORDER_UPPER_LEFT_NORM = 0
ORDER_UPPER_RIGHT_ALT = 5

_lin2xy = _ura2xy if order == ORDER_UPPER_RIGHT_ALT else _uln2xy

_brightness = 0.1


# Apply brightness factor to color
def dim(color):
    red = int(color[0] * _brightness)
    grn = int(color[1] * _brightness)
    blu = int(color[2] * _brightness)
    return (red, grn, blu)


# Set the color of a pixel at given led array position
def pixel1d(i, color):
    neo[i] = dim(color)


# Set the color of a pixel at given 2D array position
def pixel2d(x, y, color):
    pos = _lin2xy(x + y * cols, cols, rows)
    if (pos > -1) and (pos < cnt):
        pixel1d(pos, color)


# Send pixel color data to display
def show():
    global delay
    neo.write()
    if delay > 0:
        time.sleep_ms(delay)


# Clear the entire display
def clear(update=True):
    neo.fill((0, 0, 0))
    if update:
        show()


# Fill with white to check current drain
def test0():
    global test_power
    
    test_power = True
    if 'test_power' in cfg:
        test_power = cfg['test_power']

    if test_power:
        print('All white - maximum current drain')
        neo.fill((255, 255, 255))
        show()
        time.sleep(5)

    print('All white - default brightness')
    neo.fill(dim((255, 255, 255)))
    show()
    time.sleep(5)
    clear()


# check if colors are correct
def test1():
    global cnt
    print('1D pixels --> [0] = red, [1] = green, [2] = blue')
    pixel1d(0, (255, 0, 0))
    if cnt > 1:
        pixel1d(1, (0, 255, 0))
    if cnt > 2:
        pixel1d(2, (0, 0, 255))
    show()


# check if row/column order correct
def test2():
    clear()
    time.sleep(2)
    print('2D pixels --> [0,0] = red, [1,0] = green, [2,0] = blue, [max,max] = yellow')  # noqa: E501
    pixel2d(0, 0, (255, 0, 0))
    pixel2d(1, 0, (0, 255, 0))
    pixel2d(2, 0, (0, 0, 255))
    pixel2d(cols-1, rows-1, (255, 255, 0))
    show()


# check if row/column order correct
def test3():
    global cnt
    print('2D pixels --> [0,0] white, if [8,0]==[0,1] white, if [16,0]==[0,1] white')  # noqa: E501
    pixel2d(0, 0, (255, 255, 255))
    if cnt > 8:
        pixel2d(8, 0, (255, 0, 0))
        pixel2d(0, 1, (255, 255, 255))
    if cnt > 16:
        pixel2d(16, 0, (255, 0, 0))
        pixel2d(0, 1, (255, 255, 255))
    show()


# blink all pixels in 1D and 2D
def test4():
    print('1D walk')
    for pos in range(cnt):
        pixel1d(pos, (255, 255, 0))
        show()
        pixel1d(pos, (0, 0, 0))
        show()

    print('2D walk')
    for y in range(rows):
        for x in range(cols):
            pixel2d(x, y, (0, 255, 255))
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
