# Display Abstraction Layer
#   st7735 Implementation for Raspberry Pi/Pi Zero
#
# Assumes standard SPI port
#   Pi Zero always use hw port 0
#     SCLK = GPIO11
#     MOSI = GPIO9
#     MISO = dc, see below
#
# Configuration (* --> required)
#   spi_cs                - 0 if not defined, 0-->cs on GPIO8, 1-->cs on GPIO7
#   spi_dc                * dc pin number (int)
#   spi_blk               - blk pin, None if not defined
#   spi_rst               - rst pin, None if not defined
#   spi_speed             - 4000000 if not defined
#   st7735_width          - 128 if not defined
#   st7735_height         - 160 ig not defined
#   st7735_offset         - [0,0] if not defined, else [left,top]
#   st7735_rotate         - 90 if not defined [0, 90, 180, 270]
#   st7735_invert         - False if not defined, invert display
#   st7735_bgr            - False if not defined (True --> bgr, else rgb)


# Make sure we're on the right platform
import sys
import genlib as gl
if gl.platform != 'linux':
    print('This module was not written for this platform')
    sys.exit()

# import platform/device specific modules
import time
import st7735
from PIL import Image, ImageDraw

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
        port = 0
        cs = 0
        if 'spi_cs' in keys:
            cs = cfg['spi_cs']
        blk = None
        if 'spi_blk' in keys:
            blk = cfg['spi_blk']
        res = None
        if 'spi_res' in keys:
            res = cfg['spi_res']
        speed = 4_000_000
        if 'spi_speed' in keys:
            speed = cfg['spi_speed']
        # display options
        width = 128
        if 'st7735_width' in keys:
            width = cfg['st7735_width']
        height = 160
        if 'st7735_height' in keys:
            height = cfg['st7735_height']
        rotate = 90
        if 'st7735_rotate' in keys:
            rotate = cfg['st7735_rotate']
        offset = [0, 0]
        if 'st7735_offset' in keys:
            offset = cfg['st7735_offset']
        invert = False
        if 'st7735_invert' in keys:
            invert = cfg['st7735_invert']
        bgr = False
        if 'st7735_bgr' in keys:
            bgr = cfg['st7735_bgr']

        if rotate == 0 or rotate == 180:
            self.cols = width
            self.rows = height
        else:
            self.cols = height
            self.rows = width

        # initialize device
        if debug:
            print(f'display = ST7735(port={port}, cs={cs}, dc={dc}, backlight={blk}, rst={res},')
            print(f'                 width={width}, height={height}, rotation={rotate},')
            print(f'                 offset_left={offset[0]}, offset_top={offset[1]},')
            print(f'                 invert={invert}, bgr={bgr}, spi_speed_hz={speed})')

        self.display = st7735.ST7735(port=port, cs=cs, dc=dc,
            backlight=blk, rst=res, width=width, height=height,
            rotation=rotate, offset_left=offset[0], offset_top=offset[1],
            invert=invert, bgr=bgr, spi_speed_hz=speed)

        # set device defaults
        self.display.begin()
        self.image = Image.new("RGB", (self.cols, self.rows), color=self.BLACK)
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
        self.display.display(self.image)

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


def test1(display):
    display.draw.rectangle((0, 0, display.size[0]-1, display.size[1]-1), outline=display.WHITE)
#    display.pixel2d(10,10,(255,255,255))
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
    print('Raspberry Pi ST7735 DAL implementation')
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
