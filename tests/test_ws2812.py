# simple ws2812 test
# turn led 0..2 on in red, green, blue

# Make sure we're on the right platform
import sys
import genlib as gl
if gl.platform == 'linux':
    print('This program/module was not written for this platform')
    sys.exit(1)

import time
from ws2812 import WS2812

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
if 'ws2812_din' not in keys:
    print('WS2812 DIN pin not configured')
    sys.exit(1)

din = cfg['ws2812_din']
cols = cfg['ws2812_cols']
rows = cfg['ws2812_rows']
order = cfg['ws2812_pixel_order']
delay = cfg['ws2812_show_delay']
cnt = cols * rows
neo = WS2812(din, cols, rows, order, show_delay=delay)


# Fill with white to check current drain
def test0():
    test_power = True
    if 'test_power' in cfg:
        test_power = cfg['test_power']

    if test_power:
        print('All white - maximum current drain')
        save = neo.brightness
        neo.brightness = 1.0
        neo.fill((0xff, 0xff, 0xff))
        neo.show()
        time.sleep(5)
        neo.brightness = save

    print('All white - default brightness')
    neo.fill((0xff, 0xff, 0xff))
    neo.show()
    time.sleep(5)


# check if color correct
def test1():
    global cnt
    print('1D pixels --> [0] = red, [1] = green, [2] = blue')
    neo.clear()
    neo.pixel1d(0, (255, 0, 0))
    if cnt > 1:
        neo.pixel1d(1, (0, 255, 0))
    if cnt > 2:
        neo.pixel1d(2, (0, 0, 255))
    neo.show()
    time.sleep(2)


# check if row/column order correct
def test2():
    print('2D pixels --> [0,0] = red, [1,0] = green, [2,0] = blue, [max,max] = yellow')  # noqa: E501
    neo.clear()
    neo.pixel2d(0, 0, (255, 0, 0))
    neo.pixel2d(1, 0, (0, 255, 0))
    neo.pixel2d(2, 0, (0, 0, 255))
    neo.pixel2d(neo.size[0]-1, neo.size[1]-1, (255, 255, 0))
    neo.show()
    time.sleep(2)


def test3():
    global cnt
    print('2D pixels --> [0,0] white, if [8,0]==[0,1] white, if [16,0]==[0,1] white')  # noqa: E501
    neo.clear()
    neo.pixel2d(0, 0, (255, 255, 255))
    if cnt > 8:
        neo.pixel2d(8, 0, (255, 0, 0))
        neo.pixel2d(0, 1, (255, 255, 255))
    if cnt > 16:
        neo.pixel2d(16, 0, (255, 0, 0))
        neo.pixel2d(0, 1, (255, 255, 255))
    neo.show()


def test4():
    print('1D walk')
    for pos in range(neo.pixel_cnt):
        neo.pixel1d(pos, (255, 255, 0))
        neo.show()
        neo.pixel1d(pos, (0, 0, 0))
        neo.show()

    print('2D walk')
    for y in range(neo.size[1]):
        for x in range(neo.size[0]):
            neo.pixel2d(x, y, (0, 255, 255))
            neo.show()
            neo.pixel2d(x, y, (0, 0, 0))
            neo.show()


if __name__ == "__main__":
    test0()
    test1()
    test2()
    test3()
    test4()
    neo.clear()
    neo.show()
