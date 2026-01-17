# simple ws2812 test
# turn led 0..2 on in red, green, blue
import sys
import time
import genlib as gl
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
orient = cfg['ws2812_orientation']
cnt = cols * rows
neo = WS2812(din, cols, rows, orient)

# Fill with white to check current drain
def test0():
    print('All white')
    neo.fill((0xff, 0xff, 0xff))
    time.sleep(5)
    neo.clear()

# check if color correct
def test1():
    global cnt
    print('1D pixels --> [0] = red, [1] = green, [2] = blue')
    neo.pixel1d(0, (0x10, 0, 0))
    if cnt > 1:
        neo.pixel1d(1, (0, 0x10, 0))
    if cnt > 2:
        neo.pixel1d(2, (0, 0, 0x10))
    neo.show()

# check if row/column order correct
def test2():
    neo.clear()
    time.sleep(2)
    print('2D pixels --> [0,0] = red, [1,0] = green, [2,0] = blue, [max,max] = yellow')
    neo.pixel2d(0, 0, (0x20,0,0))
    neo.pixel2d(1, 0, (0x0,0x20,0))
    neo.pixel2d(2, 0, (0x0,0,0x20))
    neo.pixel2d(neo.size[0]-1, neo.size[1]-1, (0x20, 0x20, 0))
    neo.show()

def test3():
    global cnt
    print('2D pixels --> [0,0] white, if [8,0]==[0,1] white, if [16,0]==[0,1] white')
    neo.pixel2d(0, 0, (0x20, 0x20, 0x20))
    if cnt > 8:
        neo.pixel2d(8, 0, (0x20, 0x0, 0x0))
        neo.pixel2d(0, 1, (0x20, 0x20, 0x20))
    if cnt > 16:
        neo.pixel2d(16, 0, (0x20, 0x0, 0x0))
        neo.pixel2d(0, 1, (0x20, 0x20, 0x20))
    neo.show()

def test4():
    print('1D walk')
    for pos in range(neo.pixel_cnt):
        neo.pixel1d(pos, (0x20, 0x20, 0))
        neo.show()
        neo.pixel1d(pos, (0, 0, 0))
        neo.show()

    print('2D walk')
    for y in range(neo.size[1]):
        for x in range(neo.size[0]):
            neo.pixel2d(x, y, (0, 0x20, 0x20))
            neo.show()
            neo.pixel2d(x, y, (0, 0, 0))
            neo.show()
    
if __name__ == "__main__":
    test0()
    test1()
    time.sleep(5)
    test2()
    time.sleep(5)
    test3()
    time.sleep(5)
    test4()
    neo.clear()
    neo.show()
