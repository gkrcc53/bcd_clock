# Simple ST7735 display test

# Make sure we're on the right platform
import sys
import genlib as gl
if gl.platform == 'linux':
    print('This program/module was not written for this platform')
    sys.exit(1)

import time
from machine import SPI
from mpy_st7735 import ST7735
from sysfont import sysfont
import tftcolor as COLOR

print()

cfg = gl.get_board_config()
hcfg = gl.get_config('hw.cfg')
cfg |= hcfg
dcfg = gl.get_config('display.cfg')
cfg |= dcfg
keys = cfg.keys()
debug = 'debug' in keys and cfg['debug']
if debug:
    for key in sorted(keys):
        print(f'{key:<25}{cfg[key]}')
    print()

offset = [0, 0]
if 'st7735_offset' in keys:
    offset = cfg['st7735_offset']
port = cfg['spi_port']
psck = cfg['spi_scl']
psda = cfg['spi_sda']
pres = cfg['spi_res']
pdc = cfg['spi_dc']
pcs = cfg['spi_cs']
baud = 40000000
if 'spi_baud' in keys:
    baud = cfg['spi_baud']

# time program
tstart = gl.time_ms()

rotate = 0
if 'st7735_rotate' in keys:
    rotate = cfg['st7735_rotate']

# Normal initialization w/o rotation
spi = SPI(port, baudrate=baud, sck=psck, mosi=psda, miso=pdc)
tft = ST7735(spi, pdc, pres, pcs)
tft.rgb(True)
tft.initr()
if offset:
    tft._offset[0] = offset[0]
    tft._offset[1] = offset[1]
tft.rotation(rotate)

# try something simple
tft.clear()

ul = (0, 0)
lr = (tft.size[0]-1, tft.size[1]-1)
tft.line((ul[0], ul[1]), (lr[0], ul[1]), COLOR.WHITE)
tft.line((lr[0], ul[1]), (lr[0], lr[1]), COLOR.WHITE)
tft.line((lr[0], lr[1]), (ul[0], lr[1]), COLOR.WHITE)
tft.line((ul[0], lr[1]), (ul[0], ul[1]), COLOR.WHITE)

colors = [COLOR.RED, COLOR.GREEN, COLOR.BLUE, COLOR.WHITE]
for i in range(4):
    tft.rotation(i)

    msg = f'Rotation({i})'
    tft.text((3, 3), msg, colors[i], sysfont, 2, nowrap=True)
    tft.local_fill_rect((20, 20), (20, 20), colors[i])

time.sleep(5)
tft.clear()
