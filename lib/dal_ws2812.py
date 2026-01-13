# Display Abstraction Layer
#   WS2812 Implementation
#
# Configuration (* --> required)
#   display_type        * "ws2812"
#   ws2812_din          * GPIO pin used to send data to the display
#   ws2812_orientation  * 5 = UPPER_RIGHT_ALTERNATE else 0 = UPPER_LEFT_NORMAL
#   ws2812_rows         * panel row count
#   ws2812_cols         * panel column count

from ws2812 import WS2812
import rgbcolor as COLOR
import genlib as gl

class DAL(WS2812):
    RED       = COLOR.RED
    LTRED     = COLOR.LTRED
    GREEN     = COLOR.GREEN
    LTGREEN   = COLOR.LTGREEN
    BLUE      = COLOR.BLUE
    LTBLUE    = COLOR.LTBLUE
    CYAN      = COLOR.CYAN
    LTCYAN    = COLOR.LTCYAN
    MAGENTA   = COLOR.MAGENTA
    LTMAGENTA = COLOR.LTMAGENTA
    YELLOW    = COLOR.YELLOW
    LTYELLOW  = COLOR.LTYELLOW
    BLACK     = COLOR.BLACK
    WHITE     = COLOR.WHITE
    GRAY      = COLOR.GRAY
    LTGRAY    = COLOR.LTGRAY
    VLTGRAY   = COLOR.VLTGRAY
    VVLTGRAY  = COLOR.VVLTGRAY

    # Display initialization
    def __init__(self):
        cfg = gl.get_board_config()
        if 'ws2812_din' not in cfg.keys():
            print('WS2812 display not configured')
            return None
        din = cfg['ws2812_din']
        rows = cfg['ws2812_rows']
        cols = cfg['ws2812_cols']
        orient = cfg['ws2812_orientation']
        super().__init__(din, cols, rows, orient)
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
