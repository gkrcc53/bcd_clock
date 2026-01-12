# Simple SSD1306 display test
import time
from machine import Pin, I2C, SoftI2C
import lib.genlib as gl
from ssd1306 import SSD1306_I2C
import oledcolor as COLOR

cfg = gl.get_board_config()
keys = cfg.keys()

# Screen errors seen at ssd1306 freq 300000
assert('i2c_sda' in cfg.keys())
sda = Pin(cfg['i2c_sda'], Pin.OUT, Pin.PULL_UP)
scl = Pin(cfg['i2c_scl'], Pin.OUT, Pin.PULL_UP)
freq = 400_000
if 'i2c_freq' in keys:
    freq = int(cfg['i2c_freq'])
oled_width = 128
if 'ssd1306_width' in keys:
    oled_width = int(cfg['ssd1306_width'])
oled_height = 64
if 'ssd1306_height' in keys:
    oled_height = int(cfg['ssd1306_height'])
soft = 'i2c_soft' in keys and cfg['i2c_soft']
if soft:
    i2c = SoftI2C(scl=scl, sda=sda, freq=freq)
else:
    port = cfg['i2c_port']
    i2c = I2C(port, scl=scl, sda=sda, freq=freq)
oled = SSD1306_I2C(oled_width, oled_height, i2c)
oled.clear()

size = (128, 64)

def test1():
    ul=(0,0)
    lr=(size[0]-1, size[1]-1)
    oled.line(ul[0], ul[1], lr[0], ul[1], COLOR.WHITE)
    oled.line(lr[0], ul[1], lr[0], lr[1], COLOR.WHITE)
    oled.line(lr[0], lr[1], ul[0], lr[1], COLOR.WHITE)
    oled.line(ul[0], lr[1], ul[0], ul[1], COLOR.WHITE)

    msg = 'Hello SSD1306'
    oled.text(msg, 10, 3, COLOR.WHITE)
    oled.fill_rect(20, 12, 12, 12, COLOR.WHITE)
    oled.show()
    time.sleep(2)

    oled.clear()

def test2():
    oled.clear()
    
    start_x = 8
    start_y = 8
    pixel_x = 4
    pixel_y = 4
    border = 2
    
    posy = start_y
    for i in range(8):
        posx = start_x + i * (pixel_x + border)
        oled.fill_rect(posx, posy, pixel_x, pixel_y, 1)
        oled.show()
        time.sleep(0.5)

    posx = start_x
    for i in range(8):
        posy = start_y + i * (pixel_y + border)
        oled.fill_rect(posx, posy, pixel_x, pixel_y, 1)
        oled.show()
        time.sleep(0.5)

    time.sleep(2)
    oled.clear()

if __name__ == "__main__":
    test1()
    test2()
