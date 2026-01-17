# Simple ST7789 display test
from machine import SPI,Pin
import time
import genlib as gl
from st7789 import ST7789
import tftcolor as TFT
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
baud = cfg['spi_baud']
width = cfg['st7789_width']
height = cfg['st7789_height']

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
