# Display Abstraction Layer
#   ST7735 Implementation
#
# Configuration (* --> required)
#   display_type      * "st7735"
#   st7735_offset     - [0, 0] if not defined, reorder settings if necessary
#   st7735_rotate     - 0 if not defined, [0..3]
#   st7735_port       * SPI port 0..1
#   st7735_sda        * SPI mosi pin
#   st7735_scl        * SPI clock pin
#   st7735_cs         * SPI chip select pin
#   st7735_dc         * SPI miso pin
#   st7735_res        * SPI reset pin
#   st7735_baud       - 40_000_000 if not defined
#   st7735_color_rgb  - True if not defined, else RGB|BGR
#   st7735_init       - initr if not defined ["initr", "initb", "initb2", "initg"]
#
# Notes
#   display size fixed at 128x160 in driver
#   I have some displays that require a non-zero offset parameter, note that the
#   last definition in the configuration file will be active. Reorder or eliminate
#   unused offset configuration settings if necessary.

from machine import SPI
from st7735 import ST7735
import tftcolor as COLOR
import genlib as gl

class DAL(ST7735):
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
        inits = {"initr"  : self.initr,
                 "initb"  : self.initb,
                 "initb2" : self.initb2,
                 "initg"  : self.initg}
        # Get display configuration
        cfg = gl.get_board_config()
        keys = cfg.keys()
        offset = [0, 0]
        if 'st7735_offset' in keys:
            offset = cfg['st7735_offset']
        baud = 40_000_000
        if 'st7735_baud' in keys:
            baud = cfg['st7735_baud']
        port = cfg['st7735_port']
        psck = cfg['st7735_scl']
        psda = cfg['st7735_sda']
        pres = cfg['st7735_res']
        pdc = cfg['st7735_dc']
        pcs = cfg['st7735_cs']
        rotate = 0
        if 'st7735_rotate' in keys:
            rotate = cfg['st7735_rotate']
        color_rgb = True
        if 'st7735_color_rgb' in keys:
            color_rgb = cfg['st7735_color_rgb']
        init = inits['initr']
        if 'st7735_init' in keys:
            temp = cfg['st7735_init']
            if temp in inits.keys():
                init = inits[temp]

        # Normal initialization
        spi=SPI(port, baudrate=baud, sck=psck, mosi=psda, miso=pdc)
        super().__init__(spi, pdc, pres, pcs)
        self.rgb(color_rgb)
        init()
        
        # Some displays require an offset
        if offset:
            self._offset[0] = offset[0]
            self._offset[1] = offset[1]
        self.rotation(rotate)
        self.clear()
        
        # display geometry (vertical orientation)
        size = self.size
        
        # virtual pixel size
        pixel_x = size[0] // 8
        pixel_y = size[1] // 4
        pixel_size = min(pixel_x, pixel_y) & ~1

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

    # set single virtual 'pixel' at x, y to color
    def xy_set(self, x, y, color):
        posx = self.start_x + x * (self.pixel_x + self.border)
        posy = self.start_y + y * (self.pixel_y + self.border)
        super().fill_rect((posx, posy), (self.pixel_x, self.pixel_y), color)

    # set single virtual 'dot' at x, y to color
    def dot_set(self, x, y, color):
        dot_size = self.pixel_x // 2
        dot_ofs = dot_size // 2
        posx = self.start_x + dot_ofs + x * (self.pixel_x + self.border)
        posy = self.start_y + dot_ofs + y * (self.pixel_y + self.border)
        super().fill_rect((posx, posy), (dot_size, dot_size), color)

    # graphics are immediately visible
    def show(self):
        pass
    
    # convert low level API
    def hline(self, x, y, length, color):
        super().hline((x, y), length, color)

    # convert low level API
    def vline(self, x, y, length, color):
        super().vline((x, y), length, color)
