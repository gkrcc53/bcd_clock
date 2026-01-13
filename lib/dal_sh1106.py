# Display Abstraction Layer
#   SH1106 Implementation
#
# Configuration (* --> required)
#   display_type       * "sh1106"
#   i2c_soft           - If true, use SoftI2C, else i2c_port must be defined
#   i2c_port           - I2C hardware port (0|1), ignored if i2c_soft is true
#   i2c_sda            * If not SoftI2C, must be port compatible
#   i2c_scl            * If not SoftI2C, must be port compatible
#   i2c_freq           - 200_000 if not defined (my display does not work at 400000)
#   sh1106_width       - 128 if not defined
#   sh1106_height      - 64 if not defined
#   sh1106_rotate      - 0 if not defined, [0, 90, 180, 270]
#   sh1106_pwr_delay   - 100 if not defined (ms sleep after display power on|off)
#   sh1106_res         - If defined, this pin is used in init_display() and reset() toggles the pin
#
# Notes
#   If defined, the pin is toggled (HI 1ms, LO 20ms, HI 20ms) in reset(),
#   which is called when the display is initialized.

import sys
from machine import SoftI2C, I2C, Pin
from sh1106 import SH1106_I2C
import oledcolor as COLOR
import genlib as gl

class DAL(SH1106_I2C):
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
        # Get display configuration
        cfg = gl.get_board_config()
        keys = cfg.keys()
        if 'i2c_sda' not in keys:
            print('I2C communication not configured')
            sys.exit(1)
        sda = Pin(cfg['i2c_sda'], Pin.OUT, Pin.PULL_UP)
        scl = Pin(cfg['i2c_scl'], Pin.OUT, Pin.PULL_UP)
        freq = 200_000
        if 'i2c_freq' in keys:
            freq = int(cfg['i2c_freq'])
        width = 128
        if 'sh1106_width' in keys:
            width = int(cfg['sh1106_width'])
        height = 64
        if 'sh1106_height' in keys:
            height = int(cfg['sh1106_height'])
        soft = 'i2c_soft' in keys and cfg['i2c_soft']
        if soft:
            i2c = SoftI2C(scl=scl, sda=sda, freq=freq)
        else:
            port = cfg['i2c_port']
            i2c = I2C(port, scl=scl, sda=sda, freq=freq)
        rotate = 0
        if 'sh1106_rotate' in keys:
            rotate = cfg['sh1106_rotate']
        # SH1106 specs say 100ms
        delay = 100
        if 'sh1106_pwr_delay' in keys:
            delay = cfg['sh1106_pwr_delay']
        res = None
        if 'sh1106_res' in keys:
            res = Pin(cfg['sh1106_res'], Pin.OUT)
        super().__init__(width, height, i2c,
                         res=res,
                         rotate=rotate,
                         pwr_delay=delay)
        self.sleep(False)
        self.clear()
        
        # display geometry
        size = self.size
        
        # virtual pixel size
        pixel_x = size[0] // 8
        pixel_y = size[1] // 4
        pixel_size = min(pixel_x, pixel_y) & ~1

        # if virtual pixels large enough, reduce size and draw grid
        border = 0
        if pixel_size > 4:
            border = 2
            pixel_size -= 4

        self.pixel_x = pixel_size
        self.pixel_y = pixel_size
        
        self.start_x = (size[0] - (8 * (pixel_size + border))) // 2
        self.start_y = (size[1] - (4 * (pixel_size + border))) // 2

        self.border = border

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

    def show(self, show=False):
        super().show(show)

    # set single virtual 'pixel' at x, y to color
    def xy_set(self, x, y, color):
        posx = self.start_x + x * (self.pixel_x + self.border)
        posy = self.start_y + y * (self.pixel_y + self.border)
        super().fill_rect(posx, posy, self.pixel_x, self.pixel_y, color)
        
    # set single virtual 'dot' at x, y to color
    def dot_set(self, x, y, color):
        dot_size = self.pixel_x // 2
        dot_ofs = dot_size // 2
        posx = self.start_x + dot_ofs + x * (self.pixel_x + self.border)
        posy = self.start_y + dot_ofs + y * (self.pixel_y + self.border)
        super().fill_rect(posx, posy, dot_size, dot_size, color)
