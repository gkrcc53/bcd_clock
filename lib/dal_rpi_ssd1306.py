# Display Abstraction Layer
#   SH1106 Implementation for Raspberry Pi Zero 2W
#
# Configuration (* --> required)
#   display_type       * "rpi_ssd1306"
#   i2c_port           - I2C hardware port, default is 1
#   i2c_addr           - device address, 0x3c = 60 if not defined
#   i2c_sda            ! fixed to GPIO2
#   i2c_scl            ! fixed to GPIO3
#   i2c_freq           ! fixed in /boot/firmware/config.txt
#   ssd1306_width      - 128 if not defined (unrotated)
#   ssd1306_height     - 64 if not defined (unrotated)
#   ssd1306_rotate     - 0 if not defined, [0..3]
#   ssd1306_font_size  - 20 if not defined
#
# Notes
#   rotate values of 1 and 3 do not work correctly, Not sure why...

# Make sure we're on the right platform
import sys
import genlib as gl
if gl.platform != 'linux':
    print('This module was not written for this platform')
    sys.exit()

import time
from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from PIL import ImageDraw, Image, ImageFont
import oledcolor as COLOR


class DAL():
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
    def __init__(self, cfg={}):
        # Load module configuration
        dcfg = gl.get_config(f'{__name__}.cfg')
        cfg |= dcfg

        # Get merged configuration keys
        keys = cfg.keys()

        debug = 'debug' in keys and cfg['debug']
        if debug:
            print('DAL configuration')
            for key in keys:
                print(f'{key:<20}{cfg[key]}')
            print()
        self._debug = debug

        # i2c options
        port = 1
        if 'i2c_port' in keys:
            port = cfg['i2c_port']
        # ssd1306 options
        addr = 0x3c
        if 'ssd1306_addr' in keys:
            addr = cfg['ssd1306_addr']
        width = 128
        if 'ssd1306_width' in keys:
            width = cfg['ssd1306_width']
        height = 64
        if 'ssd1306_height' in keys:
            height = cfg['ssd1306_height']
        rotate = 0
        if 'ssd1306_rotate' in keys:
            rotate = cfg['ssd1306_rotate']
        fsize = 20
        if 'ssd1306_font_size' in keys:
            fsize = cfg['ssd1306_font_size']
        serial = i2c(port=port, address=addr)
        self.display = ssd1306(serial, width=width, height=height, rotate=rotate)
        if rotate == 0 or rotate == 2:
            self.cols = width
            self.rows = height
        else:
            self.cols = height
            self.rows = width
        if debug:
            print(f'display size: {self.cols}x{self.rows}')

        self.width = self.cols
        self.height = self.rows
        self.image = Image.new("1", (self.cols, self.rows), color=0)
        self.draw = ImageDraw.Draw(self.image)
        self.display.clear()
        self.display.show()

        # Get font and set scale
        self._font = ImageFont.load_default(fsize)
        self._scale = 1

        # define BCD clock geometric parameters
        # virtual pixel size
        pixel_x = self.cols // 8
        pixel_y = self.rows // 4
        pixel_size = min(pixel_x, pixel_y) & ~1

        # if virtual pixels large enough, reduce size and draw grid
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
        # simple text support
        config['text'] = True
        config['opaque_text'] = False
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
    def hline(self, x, y, len, color, show=False):
        self.draw.line([(x, y), (x+len, y)], fill=color)
        if show:
            self.show()

    # Draw a vertical line with the indicated color
    def vline(self, x, y, len, color, show=False):
        self.draw.line([(x, y), (x, y+len)], fill=color)
        if show:
            self.show()

    # Fill a rectangle with the indicated color
    def fill_rect(self, x, y, lenx, leny, color, show=False):
        self.draw.rectangle([(x, y), (x+lenx, y+leny)], fill=color)
        if show:
            self.show()

    # Fill the display with the indicated color
    def fill(self, color, show=False):
        self.fill_rect(0, 0, self.display.size[0]-1, self.display.size[1]-1, color, show)

    # set single virtual 'pixel' at x, y to color
    def xy_set(self, x, y, color):
        posx = self.start_x + x * (self.pixel_x + self.border)
        posy = self.start_y + y * (self.pixel_y + self.border)
        self.fill_rect(posx, posy, self.pixel_x, self.pixel_y, color)

    # set single virtual 'dot' at x, y to color
    def dot_set(self, x, y, color):
        dot_size = self.pixel_x // 2
        dot_ofs = dot_size // 2
        posx = self.start_x + dot_ofs + x * (self.pixel_x + self.border)
        posy = self.start_y + dot_ofs + y * (self.pixel_y + self.border)
        self.fill_rect(posx, posy, dot_size, dot_size, color)

    # Return the bounding box for the indicated text
    def text_box(self, text, scale=0):
        return self._font.getbbox(text)

    # Draw text at the specified location
    def text(self, text, x, y, color=COLOR.WHITE, scale=0):
        self.draw.text((x, y), text, font=self._font, fill=color)


def test0(display):
    display.draw.rectangle((0, 0, display.size[0]-1, display.size[1]-1), outline=display.WHITE)
    display.show()
    time.sleep(2)


def test1(display):
    display.text('DAL SSD1306', 3, 3, display.WHITE)
    display.fill_rect(30, 30, 20, 20, display.WHITE, show=True)
    time.sleep(2)
    display.clear()


def test2(display):
    cfg = display.configuration()
    start_x = cfg['start_x']
    start_y = cfg['start_y']
    pixel_x = cfg['pixel_x']
    pixel_y = cfg['pixel_y']
    border = cfg['border']

    posy = start_y
    for i in range(8):
        posx = start_x + i * (pixel_x + border)
        display.fill_rect(posx, posy, pixel_x, pixel_y, COLOR.WHITE)
        display.show()
        time.sleep(0.5)

    posx = start_x
    for i in range(1,4):
        posy = start_y + i * (pixel_y + border)
        display.fill_rect(posx, posy, pixel_x, pixel_y, COLOR.WHITE)
        display.show()
        time.sleep(0.5)

    time.sleep(2)
    display.clear()


def main():
    print('Raspberry Pi SSD1306 DAL implementation')
    cfg = gl.get_config('hw.cfg')
    dcfg = gl.get_config('display.cfg')
    cfg |= dcfg
    cfg['ssd1306_font_size'] = 12
    display = DAL(cfg)
    cfg = display.configuration()
    return display


if __name__ == "__main__":
    dsp = main()
    test0(dsp)
    test1(dsp)
    test2(dsp)
