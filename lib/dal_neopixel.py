# Display Abstraction Layer
#   NeoPixel Implementation
#
# Configuration (* --> required)
#   display_type          * "neopixel"
#   test_power            - test maximum power drain, default true
#   neopixel_din          * GPIO pin used to send data to the display
#   neopixel_pixel_order  * 5 = UPPER_RIGHT_ALTERNATE else
#                           0 = UPPER_LEFT_NORMAL
#   neopixel_rows         * panel row count
#   neopixel_cols         * panel column count
#   neopixel_brightness   - [0..1], 0.1 if not defined
#   neopixel_drive        - Pin drive value if supported, else 0
#   neopixel_show_delay   - 10ms if not defined

# Make sure we're on the right platform
import sys
import genlib as gl
if gl.platform == 'linux':
    print('This module was not written for this platform')
    sys.exit()

import time
from machine import Pin
from neopixel import NeoPixel
import rgbcolor as COLOR

ORDER_UPPER_LEFT_NORM = 0
ORDER_UPPER_RIGHT_ALT = 5


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


class DAL(NeoPixel):
    RED = COLOR.RED
    LTRED = COLOR.LTRED
    GREEN = COLOR.GREEN
    LTGREEN = COLOR.LTGREEN
    BLUE = COLOR.BLUE
    LTBLUE = COLOR.LTBLUE
    CYAN = COLOR.CYAN
    LTCYAN = COLOR.LTCYAN
    MAGENTA = COLOR.MAGENTA
    LTMAGENTA = COLOR.LTMAGENTA
    YELLOW = COLOR.YELLOW
    LTYELLOW = COLOR.LTYELLOW
    BLACK = COLOR.BLACK
    WHITE = COLOR.WHITE
    GRAY = COLOR.GRAY
    LTGRAY = COLOR.LTGRAY
    VLTGRAY = COLOR.VLTGRAY
    VVLTGRAY = COLOR.VVLTGRAY

    # Display initialization
    def __init__(self, cfg):
        keys = cfg.keys()
        if 'neopixel_din' not in keys:
            print('neopixel data pin not configured')
            return None
        din = cfg['neopixel_din']
        self.rows = cfg['neopixel_rows']
        self.cols = cfg['neopixel_cols']
        self.pixel_cnt = self.rows * self.cols
        self.brightness = 0.1
        self.show_delay = 10
        if 'neopixel_show_delay' in keys:
            self.show_delay = cfg['neopixel_show_delay']
        order = cfg['neopixel_pixel_order']
        if 'neopixel_brightness' in keys:
            bright = cfg['neopixel_brightness']
        drive = 0
        if 'neopixel_drive' in keys:
            drive = cfg['neopixel_drive']
        self._lin2xy = _ura2xy if order == ORDER_UPPER_RIGHT_ALT else _uln2xy
        dname = f'DRIVE_{drive}'
        if dname in dir(Pin):
            drive = Pin.__dict__[dname]
            dpin = Pin(din, drive=drive)
        else:
            dpin = Pin(din)
        super().__init__(dpin, self.pixel_cnt)
        self._brightness = bright
        self.clear()
        # virtual pixel size
        self.pixel_x = 2 if self.cols == 16 else 1
        self.pixel_y = self.pixel_x
        # display geometry
        self.start_x = 0
        self.start_y = 2 * self.pixel_y
        # virtual pixel border
        self.border = 0

    # Return display geometry
    def configuration(self):
        config = {}
        # clock display offset
        config['start_x'] = self.start_x
        config['start_y'] = self.start_y
        # clock virtual pixel size
        config['pixel_x'] = self.pixel_x
        config['pixel_y'] = self.pixel_y
        # clock pixel border
        config['border'] = self.border
        return config

    # Return the brightness factor
    @property
    def brightness(self):
        return self._brightness

    # Set the brightness factor
    @brightness.setter
    def brightness(self, val):
        if val < 0:
            val = 0.0
        elif val > 1.0:
            val = 1.0
        self._brightness = val

    # Return the 2D size of the display
    @property
    def size(self):
        return (self.cols, self.rows)

    # Update the display
    def show(self):
        self.write()
        if self.show_delay > 0:
            time.sleep_ms(self.show_delay)

    # set all the pixels to black
    def clear(self, show=True):
        self.fill(COLOR.BLACK)
        if show:
            self.show()

    # Apply brightness factor to color
    def dim(self, color):
        red = int(color[0] * self.brightness)
        grn = int(color[1] * self.brightness)
        blu = int(color[2] * self.brightness)
        return (red, grn, blu)

    # Set the color of a single pixel in 1d
    def pixel1d(self, pos, color):
        if (pos >= 0) and (pos < self.pixel_cnt):
            self[pos] = self.dim(color)

    # Set the color of a single pixel
    def pixel2d(self, x, y, color):
        pos = self._lin2xy(x + y * self.cols, self.cols, self.rows)
        self.pixel1d(pos, color)

    # Draw a horizontal line with the indicated color
    def hline(self, x, y, length, color, show=True):
        for i in range(length):
            self.pixel2d(x+i, y, color)
        if show:
            self.show()

    # Fill a rectangle with the indicated color
    def fill_rect(self, x, y, lx, ly, color, show=True):
        px = x
        py = y
        for i in range(ly):
            self.hline(px, py, lx, color, False)
            py += 1
        if show:
            self.show()

    # set single virtual 'pixel' at x, y to color
    def xy_set(self, x, y, color):
        if self.pixel_x == 2:
            posx = self.start_x + (x * self.pixel_x)
            posy = self.start_y + (y * self.pixel_y)
            self.fill_rect(posx, posy, self.pixel_x, self.pixel_y, color)
        else:
            self.pixel2d(self.start_x + x, self.start_y + y, color)

    # Due to resolution, 'dots' (half sized 'pixels') are not supported
    def dot_set(self, x, y, color):
        self.xy_set(x, y, color)


if __name__ == "__main__":
    import time
    import genlib as gl

    print()

    cfg = gl.get_board_config()
    hcfg = gl.get_config('hw.cfg')
    dcfg = gl.get_config('display.cfg')
    cfg = cfg | hcfg | dcfg
    display = DAL(cfg)

    test_power = True
    if 'test_power' in cfg:
        test_power = cfg['test_power']

    if test_power:
        print('All white - maximum current drain')
        # fill is low level driver - no brightness correction
        display.fill(COLOR.WHITE)
        display.show()
        time.sleep(5)

    print('All white - default brightness')
    display.fill(display.dim(COLOR.WHITE))
    display.show()
    time.sleep(5)
    display.clear()

    print('1D pixels --> [0] = red, [1] = green, [2] = blue')
    display.pixel1d(0, COLOR.RED)
    display.pixel1d(1, COLOR.GREEN)
    display.pixel1d(2, COLOR.BLUE)
    display.show()
    time.sleep(5)
    display.clear()

    print('2D pixels --> [0,0] = red, [1,0] = green, [2,0] = blue, [max,max] = yellow')
    display.pixel2d(0, 0, COLOR.LTRED)
    display.pixel2d(1, 0, COLOR.LTGREEN)
    display.pixel2d(2, 0, COLOR.LTBLUE)
    display.pixel2d(display.cols-1, display.rows-1, COLOR.LTYELLOW)
    display.show()
    time.sleep(5)
    display.clear()

    print('2D pixels --> [0,0] white, if [8,0]==[0,1] white, if [16,0]==[0,1] white')
    display.pixel2d(0, 0, COLOR.LTGRAY)
    display.pixel2d(8, 0, COLOR.LTRED)
    display.pixel2d(0, 1, COLOR.LTGRAY)
    display.pixel2d(16, 0, COLOR.LTRED)
    display.pixel2d(0, 1, COLOR.LTGRAY)
    display.show()
    time.sleep(5)
    display.clear()

    print('1D walk')
    for pos in range(display.pixel_cnt):
        display.pixel1d(pos, COLOR.LTYELLOW)
        display.show()
        display.pixel1d(pos, COLOR.BLACK)
        display.show()

    print('2D walk')
    for y in range(display.rows):
        for x in range(display.cols):
            display.pixel2d(x, y, COLOR.WHITE)
            display.show()
            display.pixel2d(x, y, COLOR.BLACK)
            display.show()
    display.clear()
