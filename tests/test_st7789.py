# Simple ST7789 display test

# Make sure we're on the right platform
import sys
import genlib as gl
if gl.platform == 'linux':
    print('This program/module was not written for this platform')
    sys.exit(1)

from machine import SPI, Pin
import time
from st7789 import ST7789
import tftcolor as COLOR
import vga2_16x32 as font

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

port = cfg['spi_port']
psck = cfg['spi_scl']
psda = cfg['spi_sda']
pres = cfg['spi_res']
pdc = cfg['spi_dc']
pcs = cfg['spi_cs']
baud = 40000000
if 'spi_baud' in keys:
    baud = cfg['spi_baud']
width = 240
if 'st7789_width' in keys:
    width = cfg['st7789_width']
height = 320
if 'st7789_height' in keys:
    height = cfg['st7789_height']
invert = False
if 'st7789_color_invert' in keys:
    invert = cfg['st7789_color_invert']

# Normal initialization w/o rotation
spi = SPI(port, baudrate=baud, sck=psck, mosi=psda, miso=pdc)
tft = ST7789(spi, width, height,
             dc=Pin(pdc, Pin.OUT),
             reset=Pin(pres, Pin.OUT),
             cs=Pin(pcs, Pin.OUT))
tft.inversion_mode(invert)

# try something simple
colors = (COLOR.RED, COLOR.GREEN, COLOR.BLUE, COLOR.WHITE)
for i in range(4):
    tft.rotation(i)

    ul = (0, 0)
    lr = (height-1, width-1) if i & 1 == 1 else (width-1, height-1)
    tft.line(ul[0], ul[1], lr[0], ul[1], colors[i])
    tft.line(lr[0], ul[1], lr[0], lr[1], colors[i])
    tft.line(lr[0], lr[1], ul[0], lr[1], colors[i])
    tft.line(ul[0], lr[1], ul[0], ul[1], colors[i])

    msg = f'Rotation({i})'
    tft.text(font, msg, 3, 3, colors[i])

    tft.local_fill_rect(40, 40, 20, 20, colors[i])

time.sleep(5)
tft.clear()
