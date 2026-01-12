# Simple ST7789 display test
from machine import SPI,Pin
import time
import genlib as gl
from st7789 import ST7789
import tftcolor as TFT
import vga2_16x32 as font

# POWER
#   GND      GND
#   VCC      3.3V

# Pin assignments
#   blk      3.3V

# ESP32 S2 mini
# port = 2
# scl = 35
# sda = 36
# res = 33
# dc = 37
# cs = 34

cfg = gl.get_board_config()
keys = cfg.keys()
debug = 'debug' in keys and cfg['debug']
if debug:
    for key in sorted(keys):
        print(f'{key:<25}{cfg[key]}')
    print()

port = cfg['st7789_port']
psck = cfg['st7789_scl']
psda = cfg['st7789_sda']
pres = cfg['st7789_res']
pdc = cfg['st7789_dc']
pcs = cfg['st7789_cs']
width = cfg['st7789_width']
height = cfg['st7789_height']
baud = cfg['st7789_baud']

# Normal initialization w/o rotation
spi=SPI(port, baudrate=baud, sck=psck, mosi=psda, miso=pdc)
tft=ST7789(spi,width,height,dc=Pin(pdc,Pin.OUT),reset=Pin(pres,Pin.OUT),cs=Pin(pcs,Pin.OUT))

# try something simple
colors = (TFT.RED, TFT.GREEN, TFT.BLUE, TFT.WHITE)
for i in range(4):
    tft.rotation(i)

    ul=(0,0)
    lr=(319,239) if i & 1 == 1 else (239,319)
    tft.line(ul[0], ul[1], lr[0], ul[1], colors[i])
    tft.line(lr[0], ul[1], lr[0], lr[1], colors[i])
    tft.line(lr[0], lr[1], ul[0], lr[1], colors[i])
    tft.line(ul[0], lr[1], ul[0], ul[1], colors[i])

    msg = f'Rotation({i})'
    tft.text(font, msg, 3, 3, colors[i])

    tft.fill_rect(40, 40, 20, 20, colors[i])
    
    time.sleep(1)

time.sleep(5)
tft.clear()
