# Simple SH1106 display test
#
# I have seen problems initializing this display, the problems seem to
# go away after a power on/off cycle.

import time
from machine import Pin, I2C
import genlib as gl
from sh1106 import SH1106_I2C
import oledcolor as COLOR

cfg = gl.get_board_config()
hcfg = gl.get_config('hw.cfg')
cfg |= hcfg
dcfg = gl.get_config('display.cfg')
cfg |= dcfg
keys = cfg.keys()

freq = cfg['i2c_freq']
width = cfg['sh1106_width']
height = cfg['sh1106_height']
delay = cfg['sh1106_pwr_delay']

i2c = I2C(cfg['i2c_port'], scl=Pin(cfg['i2c_scl']), sda=Pin(cfg['i2c_sda']), freq=freq)

def test1():
    for i in range(4):
        rotate = i * 90
        oled = SH1106_I2C(width, height, i2c, pwr_delay=delay, rotate=rotate)
        oled.sleep(False)

        ul=(0,0)
        lr=(oled.size[0]-1, oled.size[1]-1)
        oled.line(ul[0], ul[1], lr[0], ul[1], COLOR.WHITE)
        oled.line(lr[0], ul[1], lr[0], lr[1], COLOR.WHITE)
        oled.line(lr[0], lr[1], ul[0], lr[1], COLOR.WHITE)
        oled.line(ul[0], lr[1], ul[0], ul[1], COLOR.WHITE)

        msg = f'R({i*90})'
        oled.text(msg, 10, 3, COLOR.WHITE)
        oled.fill_rect(12, 12, 12, 12, COLOR.WHITE)
        oled.show()
        time.sleep(2)

    oled.clear()

def test2():
    rotate = 90
    oled = SH1106_I2C(128, 64, i2c, pwr_delay=100, rotate=rotate)
    oled.sleep(False)
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
        oled.show(True)
        time.sleep(0.5)

    posx = start_x
    for i in range(8):
        posy = start_y + i * (pixel_y + border)
        oled.fill_rect(posx, posy, pixel_x, pixel_y, 1)
        oled.show(True)
        time.sleep(0.5)

    time.sleep(2)
    oled.clear()

if __name__ == "__main__":
    test1()
    test2()
