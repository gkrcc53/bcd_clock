# Display Abstraction Layer
#   NeoPixel Implementation
#
# Configuration (* --> required)
#   display_type          * "neopixel"
#   neopixel_din          * GPIO pin used to send data to the display
#   neopixel_orientation  * 5 = UPPER_RIGHT_ALTERNATE else 0 = UPPER_LEFT_NORMAL
#   neopixel_rows         * panel row count
#   neopixel_cols         * panel column count
#   neopixel_brightness   - brightness factor, 0.1 if not defined [0..1]
#   neopixel_drive        - Pin drive value if supported, 0 if not defined

from machine import Pin
from neopixel import NeoPixel
import rgbcolor as COLOR
import genlib as gl

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

class DAL(NeoPixel):
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
    def __init__(self, cfg):
        keys = cfg.keys()
        if 'neopixel_din' not in keys:
            print('neopixel data pin not configured')
            return None
        din = cfg['neopixel_din']
        self.rows = cfg['neopixel_rows']
        self.cols = cfg['neopixel_cols']
        self._pixel_cnt = self.rows * self.cols
        self.brightness = 0.1
        orient = cfg['neopixel_orientation']
        if 'neopixel_brightness' in keys:
            bright = cfg['neopixel_brightness']
        drive = 0
        if 'neopixel_drive' in keys:
            drive = cfg['neopixel_drive']
        self._lin2xy = _ura2xy if orient == ORIENTATION_UPPER_RIGHT_ALT else _uln2xy
        dname = f'DRIVE_{drive}'
        if dname in dir(Pin):
            drive = Pin.__dict__[dname]
            dpin = Pin(din, drive=drive)
        else:
            dpin = Pin(din)
        super().__init__(dpin, self._pixel_cnt)
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
        return(self.cols, self.rows)

    # Update the display
    def show(self):
        self.write()

    # set all the pixels to black
    def clear(self, show=True):
        self.fill((0,0,0))
        if show:
            self.show()

    # Set the color of a single pixel
    def pixel2d(self, x, y, color):
        pos = self._lin2xy(x + y * self.cols, self.cols, self.rows)
        if (pos > -1) and (pos < self._pixel_cnt):
            dimmer = (int(color[0]*self.brightness), int(color[1]*self.brightness), int(color[2]*self.brightness))
            self[pos] = dimmer

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
