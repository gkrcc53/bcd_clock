# Display Abstraction Layer
#   SH1106 Implementation
#
# Configuration (* --> required)
#   display_type     * "sh1106"
#   i2c_soft         - use SoftI2C, else i2c_port must be defined
#   i2c_port         - I2C port (0|1), ignored if i2c_soft is true
#   i2c_sda          * If not SoftI2C, must be port compatible
#   i2c_scl          * If not SoftI2C, must be port compatible
#   i2c_freq         - 200_000 if not defined (my display does not
#                      work at 400000)
#   sh1106_width     - 128 if not defined
#   sh1106_height    - 64 if not defined
#   sh1106_rotate    - 0 if not defined, [0, 90, 180, 270]
#   sh1106_pwr_delay - 100, else ms sleep after display power on|off
#   sh1106_res       - If defined, this pin is toggled
#                      (HI 1ms, LO 20ms, HI 20ms) in reset(),
#                      which is called during initialization

# Make sure we're on the right platform
import sys
import genlib as gl
if gl.platform == 'linux':
    print('This module was not written for this platform')
    sys.exit()

from machine import SoftI2C, I2C, Pin
from sh1106 import SH1106_I2C
import oledcolor as COLOR


class DAL(SH1106_I2C):
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

        self.i2c = i2c
        self.rotate = rotate

        # display geometry
        size = self.size

        # simple text scaling
        self._scale = 1 if size[0] < 128 else 2

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
        # simple text support
        config['text'] = True
        return config

    def show(self, full=True):
        super().local_show(full_update=full)

    # Fill the display with the indicated color
    def fill(self, color, show=False):
        super().fill(color)
        if show:
            self.show()

    # Fill a rectangle with the indicated color
    def fill_rect(self, x, y, lx, ly, color, show=False):
        super().fill_rect(x, y, lx, ly, color)
        if show:
            self.show()

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

    # Return the bounding box for the indicated text
    def text_box(self, text, scale=0):
        lscale = self._scale if scale <= 0 else scale
        return [0, 0, 8 * len(text) * lscale, 8 * lscale]

    # Draw text at the specified location
    def text(self, text, x, y, color=1, scale=0):
        lscale = self._scale if scale <= 0 else scale
        super().text_scaled(text, x, y, color=color, scale=lscale)


def test1(display):
    ul = (0, 0)
    lr = (display.size[0]-1, display.size[1]-1)
    display.line(ul[0], ul[1], lr[0], ul[1], COLOR.WHITE)
    display.line(lr[0], ul[1], lr[0], lr[1], COLOR.WHITE)
    display.line(lr[0], lr[1], ul[0], lr[1], COLOR.WHITE)
    display.line(ul[0], lr[1], ul[0], ul[1], COLOR.WHITE)

    msg = f'R({display.rotate})'
    display.text(msg, 10, 3, color=COLOR.WHITE, scale=1)
    display.fill_rect(20, 20, 12, 12, COLOR.WHITE)
    display.show()
    time.sleep(2)

    display.clear()


def test2(display):
    dcfg = display.configuration()
    start_x = dcfg['start_x']
    start_y = dcfg['start_y']
    pixel_x = dcfg['pixel_x']
    pixel_y = dcfg['pixel_y']
    border = dcfg['border']

    posy = start_y
    for i in range(8):
        posx = start_x + i * (pixel_x + border)
        display.fill_rect(posx, posy, pixel_x, pixel_y, 1)
        display.show(True)
        time.sleep(0.5)

    posx = start_x
    for i in range(1, 4):
        posy = start_y + i * (pixel_y + border)
        display.fill_rect(posx, posy, pixel_x, pixel_y, 1)
        display.show(True)
        time.sleep(0.5)

    time.sleep(2)
    display.clear()


if __name__ == "__main__":
    import time
    import genlib as gl

    print()

    cfg = gl.get_board_config()
    cfg |= gl.get_config('hw.cfg')
    cfg |= gl.get_config('display.cfg')
    display = DAL(cfg)

    test1(display)
    test2(display)
