# Display Abstraction Layer
#   st7789 Implementation for Raspberry Pi/Pi Zero
#
# A slightly modified version of the low level system driver is
# available to support displays with "inverted" colors. See the
# repository file zero/st7789.py for an example.
#
# Assumes standard SPI port
#   Pi Zero always use hw port 0
#     SCLK = GPIO11
#     MOSI = GPIO9
#     MISO = GPIO24
#     RST = GPIO25
#     CS = GPIO8
#
# Configuration (* --> required)
#   spi_cs        - 0 if not defined, 0-->cs on GPIO8, 1-->cs on GPIO7
#   spi_dc        * dc pin number (int)
#   spi_blk       - backlight pin
#                   not used by this driver, short to 3.3V
#   spi_rst       - rst pin, None if not defined
#   spi_speed     - not used in this driver
#                   optinally set in /boot/firmware/config.txt
#   st7789_width  - 240 if not defined
#   st7789_height - 320 if not defined
#   st7789_offset - [0,0] if not defined, else [left,top]
#   st7789_rotate - 90 if not defined [0, 90, 180, 270]
#   st7789_invert - False if not defined or unsupported, invert colors
#   st7789_bgr    - False if not defined (True --> bgr, else rgb)


# Make sure we're on the right platform
import sys
import genlib as gl
if gl.platform != 'linux':
    print('This module was not written for this platform')
    sys.exit()

# import platform/device specific modules
import time
from PIL import Image, ImageDraw
import board
import digitalio
import inspect

# Modified to support invert option
from adafruit_rgb_display import st7789

# normal tuple color definitions
import rgbcolor as COLOR


# might derive from some super-class
class DAL(object):
    # redefine color constants
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
    def __init__(self, cfg=None):
        # get and optionally display configuration
        keys = {}
        if cfg is not None:
            keys = sorted(cfg.keys())
        debug = 'debug' in cfg and cfg['debug']
        if debug:
            print('DAL configuration')
            for key in keys:
                print(f'{key:<20}{cfg[key]}')
            print()
        # get device specific configuration settings
        # required keys first
        if 'spi_dc' not in keys:
            raise Exception('Required configuration key "spi_dc" not defined')
        dc = int(cfg['spi_dc'])
        # SPI options
        cs = 0
        if 'spi_cs' in keys:
            cs = cfg['spi_cs']
#        blk = None
#        if 'spi_blk' in keys:
#            blk = cfg['spi_blk']
        res = None
        if 'spi_res' in keys:
            res = int(cfg['spi_res'])
#        speed = 4_000_000
#        if 'spi_speed' in keys:
#            speed = cfg['spi_speed']
        # display options
        width = 240
        if 'st7789_width' in keys:
            width = cfg['st7789_width']
        height = 320
        if 'st7789_height' in keys:
            height = cfg['st7789_height']
        rotate = 90
        if 'st7789_rotate' in keys:
            rotate = cfg['st7789_rotate']
        invert = False
        if 'st7789_invert' in keys:
            invert = cfg['st7789_invert']

        if rotate == 0 or rotate == 180:
            self.cols = width
            self.rows = height
        else:
            self.cols = height
            self.rows = width

        # initialize device
        spi = board.SPI()
        if cs == 1:
            cs_pin = digitalio.DigitalInOut(board.CE1)
        else:
            cs_pin = digitalio.DigitalInOut(board.CE0)

        # complicated, but st7735 needs pin numbers (int)
        dc_pin = None
        for val in dir(board):
            pin = getattr(board, val)
            if 'id' in dir(pin) and pin.id == dc:
                dc_pin = digitalio.DigitalInOut(pin)
                break
        if dc_pin is None:
            raise Exception(f'Couldn\'t initialize spi_dc pin {dc}')

        rst_pin = None
        if res is not None:
            for val in dir(board):
                pin = getattr(board, val)
                if 'id' in dir(pin) and pin.id == res:
                    rst_pin = digitalio.DigitalInOut(pin)
                    break
            if rst_pin is None:
                raise Exception(f'Couldn\'t initialize spi_res pin {res}')

        if debug:
            print(f'display = ST7789(spi, dc_pin, cs_pin, rst_pin, width={width}, height={height},')
            print(f'                 rotation={rotate}, invert={invert}')

        if invert:
            init_keys = list(inspect.signature(st7789.ST7789).parameters.keys())
            if 'invert' in init_keys:
                self.display = st7789.ST7789(spi, dc_pin, cs_pin, rst_pin,
                                             width=width, height=height,
                                             rotation=rotate, invert=invert)
            else:
                print('You must modify the system driver to support inverted colors')
        else:
            self.display = st7789.ST7789(spi, dc_pin, cs_pin, rst_pin,
                                         width=width, height=height,
                                         rotation=rotate)
            
        if rotate % 180 == 90:
            self.cols = height
            self.rows = width
        else:
            self.cols = width
            self.rows = height

        # Initialize PIL classes
        self.image = Image.new("RGB", (self.cols, self.rows))
        self.draw = ImageDraw.Draw(self.image)

        # clear device
        self.clear()

        # define BCD clock geometric parameters
        pixel_x = self.cols // 8
        pixel_y = self.rows // 4
        pixel_size = min(pixel_x, pixel_y) & ~1
        border = 0
        if pixel_size > 4:
            border = 2
            pixel_size -= 4

        self.pixel_x = pixel_size
        self.pixel_y = pixel_size

        self.start_x = (self.cols - (8 * (pixel_size + border))) // 2
        self.start_y = (self.rows - (4 * (pixel_size + border))) // 2

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

    # Return the 2D size of the display
    @property
    def size(self):
        return (self.cols, self.rows)

    # Update the display
    # Some displays just modify a buffer/image that needs to be sent to the device
    def show(self):
        self.display.image(self.image)

    # set all the pixels in the display to black
    def clear(self, show=True):
        self.fill(COLOR.BLACK, show)

    # Set the color of a pixel at a 2D location w/o update
    # Assume (0,0) is at upper left of display
    def pixel2d(self, x, y, color):
        self.draw.point([(x, y)], fill=color)

    # Draw a horizontal line with the indicated color
    def hline(self, x, y, length, color, show=True):
        if length == 0:
            return
        dir = 1
        if length < 0:
            dir = -1
            length = -length
        for i in range(length):
            self.pixel2d(x+i*dir, y, color)
        if show:
            self.show()

    # Draw a vertical line with the indicated color
    def vline(self, x, y, length, color, show=True):
        if length == 0:
            return
        dir = 1
        if length < 0:
            dir = -1
            length = -length
        for i in range(length):
            self.pixel2d(x, y+i*dir, color)
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

    # Fill the display with the indicated color
    def fill(self, color, show=True):
        self.fill_rect(0, 0, self.cols, self.rows, color, show)

    # set single virtual 'pixel' at x, y to color w/o update
    def xy_set(self, x, y, color):
        if self.pixel_x > 1 or self.pixel_y > 1:
            posx = self.start_x + x * (self.pixel_x + self.border)
            posy = self.start_y + y * (self.pixel_y + self.border)
            self.fill_rect(posx, posy, self.pixel_x, self.pixel_y, color, False)
        else:
            self.pixel2d(self.start_x + x, self.start_y + y, color)

    # Set virtual 'dot' to the given color
    # Assumed dots are helf sized square pixels
    def dot_set(self, x, y, color):
        if self.pixel_x <= 2 and self.pixel_y <= 2:
            self.xy_set(x, y, color)
        else:
            dot_size = self.pixel_x // 2
            dot_ofs = dot_size // 2
            posx = self.start_x + dot_ofs + x * (self.pixel_x + self.border)
            posy = self.start_y + dot_ofs + y * (self.pixel_y + self.border)
            self.fill_rect(posx, posy, dot_size, dot_size, color)

    def text(self, text, x, y, color, scale=1):
        opaque = (color[0], color[1], color[2], 0)
        self.draw.text((x, y), text, font=self.font, fill=opaque)


def test1(display):
    display.draw.rectangle((0, 0, display.size[0]-1, display.size[1]-1), outline=display.WHITE)
    display.show()
    time.sleep(5)
    display.clear()


def test2(display):
    start_x = 8
    start_y = 8
    pixel_x = 12
    pixel_y = 12
    border = 2

    posy = start_y
    for i in range(8):
        posx = start_x + i * (pixel_x + border)
        display.fill_rect(posx, posy, pixel_x, pixel_y, COLOR.WHITE)
        display.show()
        time.sleep(0.5)

    posx = start_x
    for i in range(4):
        posy = start_y + i * (pixel_y + border)
        display.fill_rect(posx, posy, pixel_x, pixel_y, COLOR.WHITE)
        display.show()
        time.sleep(0.5)

    time.sleep(2)
    display.clear()


def main():
    print('Raspberry Pi ST7789 DAL implementation')
    cfg = gl.get_config('hw.cfg')
    dcfg = gl.get_config('display.cfg')
    cfg |= dcfg
    display = DAL(cfg)
    print(f'display size: {display.size[0]}x{display.size[1]}')
    cfg = display.configuration()
    print(f'clock cfg: {cfg}')
    return display


if __name__ == "__main__":
    dsp = main()
    test1(dsp)
    test2(dsp)
