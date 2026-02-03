# Display Abstraction Layer
#   WS2812 Implementation
#
# Configuration (* --> required)
#   display_type        * "ws2812"
#   test_power          - test maximum power drain, default true
#   ws2812_din          * GPIO pin used to send data to the display
#   ws2812_pixel_order  * 5 = UPPER_RIGHT_ALTERNATE else
#                         0 = UPPER_LEFT_NORMAL
#   ws2812_rows         * panel row count
#   ws2812_cols         * panel column count
#   ws2812_brightness   - [0..1], 0.1 if not defined

# Make sure we're on the right platform
import sys
import genlib as gl
if gl.platform == 'linux':
    print('This module was not written for this platform')
    sys.exit()

from ws2812 import WS2812
import rgbcolor as COLOR


class DAL(WS2812):
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
        if 'ws2812_din' not in keys:
            print('WS2812 display not configured')
            return None
        din = cfg['ws2812_din']
        rows = cfg['ws2812_rows']
        cols = cfg['ws2812_cols']
        order = cfg['ws2812_pixel_order']
        delay = 10
        if 'ws2812_show_delay' in keys:
            delay = cfg['ws2812_show_delay']
        if 'ws2812_brightness' in keys:
            bright = cfg['ws2812_brightness']
        super().__init__(din, cols, rows, order, delay)
        self.brightness = bright
        self.clear()
        # virtual pixel size
        self.pixel_x = 2 if cols == 16 else 1
        self.pixel_y = 2 if rows == 16 else 1
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

    # apply brightness factor to color
    def dimmer(self, color):
        red = int(color[0] * self.brightness)
        grn = int(color[1] * self.brightness)
        blu = int(color[2] * self.brightness)
        return (red, grn, blu)

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
        save = display.brightness
        display.brightness = 1.0
        display.fill(COLOR.WHITE)
        display.show()
        display.brightness = save
        time.sleep(5)

    print('All white - default brightness')
    display.fill(COLOR.WHITE)
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
