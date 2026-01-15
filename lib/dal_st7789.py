# Display Abstraction Layer
#   st7789 Implementation
#
# Configuration (* --> required)
#   display_type        * "st7789"
#   st7789_width        * limited choice, see below
#   st7789_height       * limited choice, see below
#   st7789_rotate       - [0]..3
#   st7789_color_rgb    - False if not defined else RGB|BGR
#   st7789_color_invert - False if not defined
#   spi_port            * SPI port 0..1
#   spi_sda             * SPI mosi pin
#   spi_scl             * SPI sck pin
#   spi_cs              * SPI cs pin
#   spi_dc              * SPI miso pin
#   spi_res             * SPI reset pin
#   spi_baud            - 40_000_000 if not defined
#
# Notes
#   Limited choice in display sizes; 240x320, 240x240, 135x240, 128x128

from machine import SPI, Pin
from st7789 import ST7789
import tftcolor as COLOR
import genlib as gl

class DAL(ST7789):
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

    RGB = 0
    BGR = 8

    # Display initialization
    def __init__(self):
        # Get display configuration
        cfg = gl.get_board_config()
        keys = cfg.keys()
        baud = 40_000_000
        if 'spi_baud' in keys:
            baud = cfg['spi_baud']
        port = cfg['spi_port']
        psck = cfg['spi_scl']
        psda = cfg['spi_sda']
        pres = cfg['spi_res']
        pdc = cfg['spi_dc']
        pcs = cfg['spi_cs']
        rotate = 0
        if 'st7789_rotate' in keys:
            rotate = cfg['st7789_rotate']
        width = cfg['st7789_width']
        height = cfg['st7789_height']
        color_rgb = False
        if 'st7789_color_rgb' in keys:
            color_rgb = cfg['st7789_color_rgb']
        color = self.RGB if color_rgb else self.BGR
        invert = False
        if 'st7789_color_invert' in keys:
            invert = cfg['st7789_color_invert']

        # Normal initialization
        spi=SPI(port, baudrate=baud, sck=psck, mosi=psda, miso=pdc)
        super().__init__(spi, width, height,
                         dc=Pin(pdc,Pin.OUT), reset=Pin(pres,Pin.OUT), cs=Pin(pcs,Pin.OUT),
                         rotation=rotate, color_order=color)
        self.rotate = rotate
        self.inversion_mode(invert)
        self.clear()

        # get display geometry
        # compensate for rotation
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

    # Return rotation dependent geometry
    @property
    def size(self):
        return(self.width, self.height)

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

    # low level graphics immediately visible
    def show(self):
        pass
