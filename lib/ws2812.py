# Original Code from Tony Goodhew 25th March 2022
#
# GKR 03.01.25
#   Modified to support arbitrary 2D boards
#   Added start() to initialize pin and geometry
#   Assume 1st pixel is upper left, linear position snakes in 2D
# GKR 05.01.25
#   Created class structure
#   Added pixel orientation support

import array
import time
from machine import Pin
import rp2
import rgbcolor as RGB

# ============= Neopixel driver from Raspberry Pi Pico Guide =============

# ruff: disable [F821]
@rp2.asm_pio(sideset_init=rp2.PIO.OUT_LOW, out_shiftdir=rp2.PIO.SHIFT_LEFT, autopull=True, pull_thresh=24)
def ws2812():
    T1 = 2
    T2 = 5
    T3 = 3
    wrap_target()
    label("bitloop")
    out(x, 1)               .side(0)    [T3 - 1]
    jmp(not_x, "do_zero")   .side(1)    [T1 - 1]
    jmp("bitloop")          .side(1)    [T2 - 1]
    label("do_zero")
    nop()                   .side(0)    [T2 - 1]
    wrap()
# ruff: enable [F821]

# Technically, there are (at least) 8 orientations
# Starting pixel on one of four corners (first 2 bits)
#   00 - upper left
#   01 - upper right
#   10 - lower left
#   11 - lower right
# Normal or alternating transition to next row (3rd bit)
#   0 - normal (first pixel of row always on starting side)
#   1 - alternating (first pixel on alternating sides)
#
# Practically, I have only worked with (and implemented) the following;
ORIENTATION_UPPER_LEFT_NORM = 0
ORIENTATION_UPPER_RIGHT_ALT = 5

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

class WS2812():
    def __init__(self, din, cols, rows, orientation):
        self._debug = False
        self.din = din
        self.cols = cols
        self.rows = rows
        self._lin2xy = _ura2xy if orientation == ORIENTATION_UPPER_RIGHT_ALT else _uln2xy
        self._pixel_cnt = cols * rows
        self.sm = rp2.StateMachine(0, ws2812, freq=8_000_000, sideset_base=Pin(din))
        self.sm.active(1)
        self.buffer = array.array("I", [0 for _ in range(self._pixel_cnt)])
        self.dimmer = array.array("I", [0 for _ in range(self._pixel_cnt)])
        self._brightness = 0.1

    @property
    def pixel_cnt(self):
        return self._pixel_cnt

    @property
    def size(self):
        return (self.cols, self.rows)

    @property
    def debug(self):
        return self._debug
    
    @debug.setter
    def debug(self, val):
        self._debug = val

    @property
    def brightness(self):
        return self._brightness
    
    @brightness.setter
    def brightness(self, val):
        if val < 0:
            val = 0.0
        elif val > 1.0:
            val = 1.0
        self._brightness = val

    def show(self):
        factor = self._brightness
        for i,c in enumerate(self.buffer):
            r = int(((c >> 8) & 0xFF) * factor)
            g = int(((c >> 16) & 0xFF) * factor)
            b = int((c & 0xFF) * factor)
            self.dimmer[i] = (g<<16) + (r<<8) + b
        self.sm.put(self.dimmer, 8)
        time.sleep_ms(10)

    # Set the color of a pixel at given led array position
    def pixel1d(self, i, color):
        self.buffer[i] = (color[1]<<16) + (color[0]<<8) + color[2]
        
    # Set the color of a pixel at given 2D array position
    def pixel2d(self, x, y, color):
        pos = self._lin2xy(x + y * self.cols, self.cols, self.rows)
        if (pos > -1) and (pos < self._pixel_cnt):
            self.pixel1d(pos, color)

    # Set the color of the entire led array
    def fill(self, color, show=True):
        for i in range(self._pixel_cnt):
            self.pixel1d(i, color)
        if show:
            self.show()

    # Clear the entire led array (set to BLACK)
    def clear(self, show=True):
        self.fill((0, 0, 0), show)

    # Draw the border of a square with the given color
    def square(self, x, y, s, color, show=True):
        for i in range(x, x+s):
            self.pixel2d(i, y, color)
            self.pixel2d(i, y+s-1, color)
        for i in range(y+1, y+s):
            self.pixel2d(x, i, color)
            self.pixel2d(x+s-1, i, color)
        if show:
            self.show()
    
    # Draw a filled rectangle with the given color
    def fill_rect(self, x, y, lx, ly, color, show=True):
        px = x
        py = y
        for i in range(ly):
            self.hline(px, py, lx, color, False)
            py += 1
        if show:
            self.show()

    # Draw a vertical line at (x,y), length pixels long with the given color
    def vline(self, x, y, length, color, show=True):
        for i in range(length):
            self.pixel2d(x, y+i, color)
        if show:
            self.show()

    # Draw a horizontal line at (x,y), length pixels long with the given color
    def hline(self, x, y, length, color, show=True):
        for i in range(length):
            self.pixel2d(x+i, y, color)
        if show:
            self.show()

    # Draw a line from (x0, y0) to (x1, y1) with the given color
    def line(self, x0, y0, x1, y1, color, show=True):
        dx = abs(x1 - x0)
        sx = 1 if x0 < x1 else -1
        dy = -abs(y1 - y0)
        sy = 1 if y0 < y1 else -1
        error = dx + dy
        
        while True:
            self.pixel2d(x0, y0, color)
            e2 = 2 * error
            if e2 >= dy:
                if x0 == x1:
                    break
                error = error + dy
                x0 = x0 + sx
            if e2 <= dx:
                if y0 == y1:
                    break
                error = error + dx
                y0 = y0 + sy
        if show:
            self.show()

# test code utilities
def color_chase(panel, color):
    for i in range(panel.pixel_cnt):
        panel.pixel1d(i, color)
        panel.show()
 
def wheel(index):
    # Input a value 0 to 255 to get a color value.
    # The colours are a transition r - g - b - back to r.
    if index < 0 or index > 255:
        return (0, 0, 0)
    if index < 85:
        return (255 - index * 3, index * 3, 0)
    if index < 170:
        index -= 85
        return (0, 255 - index * 3, index * 3)
    index -= 170
    return (index * 3, 0, 255 - index * 3)
  
def rainbow_cycle(panel):
    for j in range(255):
        for i in range(panel.pixel_cnt):
            rc_index = (i * 256 // panel.pixel_cnt) + j
            panel.pixel1d(i, wheel(rc_index & 255))
        panel.show()
    
if __name__ == "__main__":
    from random import randint
    import genlib as gl
    
    cfg = gl.get_board_config()
    keys = cfg.keys()
    
    din = cfg['ws2812_din']
    cols = cfg['ws2812_cols']
    rows = cfg['ws2812_rows']
    orient = cfg['ws2812_orientation']
    
    # Initialize 256 LED array
    print('Initialization')
    panel = WS2812(din, cols, rows, orient)
    cnt = panel.pixel_cnt
    panel.show()

    # Set first pixels to test color order and coordinate transformation
    print('Color test [0]=red, [1]=green, [2]=blue, [0,1]=yellow')
    panel.pixel2d(0, 0, (0x20,0,0))
    panel.pixel2d(1, 0, (0x0,0x20,0))
    panel.pixel2d(2, 0, (0x0,0,0x20))
    panel.pixel2d(0, 1, (0x20, 0x20, 0))
    panel.show()
    time.sleep(1)

    print('Horizontal and vertical lines')
    panel.clear()
    for xx in range(0,panel.size[0],2):    
        panel.vline(xx,0,panel.size[1],(128,0,0))
        panel.vline(xx+1,0,panel.size[1],(0,0,128))
    panel.show()
    time.sleep(1)

    for yy in range(0,panel.size[1],2):    
        panel.hline(0,yy,panel.size[0],(128,0,0))
        panel.hline(0,yy+1,panel.size[0],(0,0,128))
    panel.show()
    time.sleep(1)

    print('Squares')
    panel.clear()
    panel.square(0,0,panel.size[0],(0,128,0))
    time.sleep(1)
    panel.square(1,1,6,(128,128,0))
    time.sleep(1)
    panel.square(2,2,4,(128,0,0))
    time.sleep(1)
    panel.square(3,3,2,(0,0,128))
    time.sleep(2)
    panel.square(0,0,4,(128,0,0))
    time.sleep(1)
    panel.square(4,4,4,(128,0,0))
    time.sleep(1)
    panel.square(4,0,4,(0,0,128))
    time.sleep(1)
    panel.square(0,4,4,(0,0,128))
    time.sleep(1)
    panel.square(2,2,4,(0,128,0))
    time.sleep(1)
    
    # Basic color values
    COLORS = (RGB.BLACK, RGB.RED, RGB.YELLOW, RGB.GREEN, RGB.CYAN, RGB.BLUE, RGB.MAGENTA, RGB.WHITE)

    print("Fills")
    for color in COLORS:       
        panel.fill(color, True)
        time.sleep(1)

    print("Chases")
    for color in COLORS:       
        color_chase(panel, color)

    print("Rainbow")
    rainbow_cycle(panel)

    print("Random lines")
    panel.clear()
    for i in range(20):
        x0 = randint(0, panel.size[0])
        y0 = randint(0, panel.size[1])
        x1 = randint(0, panel.size[0])
        y1 = randint(0, panel.size[1])
        if x0 != x1 or y0 != y1:
            color = wheel(randint(0,255))
            panel.line(x0, y0, x1, y1, (color[0], color[1], color[2]))
            time.sleep(0.5)

    time.sleep(1)
    panel.clear()
    print("\nAll done ##############")
