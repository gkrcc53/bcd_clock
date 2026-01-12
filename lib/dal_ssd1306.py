# Display Abstraction Layer
#   SSD1306 Implementation
#
# Configuration (* --> required)
#   display_type         * "ssd1306"
#   i2c_soft             - If true, use SoftI2C, else i2c_port must be defined
#   i2c_port             - I2C hardware port (0|1), ignored if i2c_soft is true
#   i2c_sda              * If not SoftI2C, must be port compatible
#   i2c_scl              * If not SoftI2C, must be port compatible
#   i2c_freq             - 400_000 if not defined
#   ssd1306_addr         - 0x3c if not defined
#   ssd1306_width        - 128 if not defined
#   ssd1306_height       - 64 if not defined
#   ssd1306_external_vcc - False if not defined

import sys
from machine import SoftI2C, I2C, Pin
from ssd1306 import SSD1306_I2C
import oledcolor as COLOR
import genlib as gl

class DAL(SSD1306_I2C):
    BLACK     = COLOR.BLACK
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
    WHITE     = COLOR.WHITE
    GRAY      = COLOR.GRAY
    YELLOW    = COLOR.YELLOW
    LTYELLOW  = COLOR.LTYELLOW
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
        freq = 400_000
        if 'i2c_freq' in keys:
            freq = int(cfg['i2c_freq'])
        width = 128
        if 'ssd1306_width' in keys:
            width = int(cfg['ssd1306_width'])
        height = 64
        if 'ssd1306_height' in keys:
            height = int(cfg['ssd1306_height'])
        soft = 'i2c_soft' in keys and cfg['i2c_soft']
        if soft:
            i2c = SoftI2C(scl=scl, sda=sda, freq=freq)
        else:
            port = cfg['i2c_port']
            i2c = I2C(port, scl=scl, sda=sda, freq=freq)
        ext_vcc = False
        if 'ssd1306_external_vcc' in keys:
            ext_vcc = cfg['ssd1306_external_vcc']
        addr = 0x3C
        if 'ssd1306_addr' in keys:
            addr = cfg['ssd1306_addr']
        super().__init__(width, height, i2c,
                         addr=addr,
                         external_vcc=ext_vcc)
        self.clear()
        
        # display geometry
        # virtual pixel size
        pixel_x = width // 8
        pixel_y = height // 4
        pixel_size = min(pixel_x, pixel_y) & ~1

        # if virtual pixels large enough, reduce size and draw grid
        border = 0
        if pixel_size > 4:
            border = 2
            pixel_size -= 4

        self.pixel_x = pixel_size
        self.pixel_y = pixel_size
        
        self.start_x = (width - (8 * (pixel_size + border))) // 2
        self.start_y = (height - (4 * (pixel_size + border))) // 2

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
