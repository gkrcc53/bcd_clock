# Display Abstraction Layer
#   Empty Implementation
#
#   A new DAL implementation can be simply made by defining the
#   __init__ and pixel2D functions. If the implementation is derived
#   from a class that implements some of the other functions, the super
#   class functions should probably be used...
#
# Configuration (* --> required)
#   display_type          * "empty"

# import platform/device specific modules
# example color definitions
import rgbcolor as COLOR

# usually need genlib
import genlib as gl


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

        # get device specific configuration settings
        self.cols = 1
        self.rows = 1
        if debug:
            print(f'display size: {self.cols}x{self.rows}')

        # initialize device/superclass
        # set device defaults
        # clear device
        # define BCD clock parameters
        self.pixel_x = 2 if self.cols == 16 else 1
        # doesn't have to be square...
        self.pixel_y = self.pixel_x
        # display geometry
        self.start_x = 0
        self.start_y = 0
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
        # simple text support
        config['text'] = False
        config['opaque_text'] = False
        return config

    # Return the 2D size of the display
    @property
    def size(self):
        return (self.cols, self.rows)

    # Update the display
    # Some displays just modify a buffer or
    # image that needs to be sent to the device
    def show(self):
        pass

    # set all the pixels in the display to black
    def clear(self, show=True):
        self.fill(COLOR.BLACK, show)

    # Set the color of a pixel at a 2D location
    # Assume (0,0) is at upper left of display
    def pixel2d(self, x, y, color):
        pass

    # Draw a horizontal line with the indicated color
    def hline(self, x, y, length, color, show=False):
        for i in range(length):
            self.pixel2d(x+i, y, color)
        if show:
            self.show()

    # Draw a vertical line with the indicated color
    def vline(self, x, y, length, color, show=False):
        for i in range(length):
            self.pixel2d(x, y+i, color)
        if show:
            self.show()

    # Fill a rectangle with the indicated color
    def fill_rect(self, x, y, lx, ly, color, show=False):
        px = x
        py = y
        for i in range(ly):
            self.hline(px, py, lx, color, False)
            py += 1
        if show:
            self.show()

    # Fill the display with the indicated color
    def fill(self, color, show=False):
        self.fill_rect(0, 0, self.cols-1, self.rows-1, color, show)

    # set single virtual 'pixel' at x, y to color
    def xy_set(self, x, y, color):
        if self.pixel_x > 1 or self.pixel_y > 1:
            posx = self.start_x + (x * self.pixel_x)
            posy = self.start_y + (y * self.pixel_y)
            self.fill_rect(posx, posy, self.pixel_x, self.pixel_y, color)
        else:
            self.pixel2d(self.start_x + x, self.start_y + y, color)

    # Due to resolution, 'dots' (half sized 'pixels') are not supported
    def dot_set(self, x, y, color):
        if self.pixel_x <= 2 and self.pixel_y <= 2:
            self.xy_set(x, y, color)
        else:
            dot_size = self.pixel_x // 2
            dot_ofs = dot_size // 2
            posx = self.start_x + dot_ofs + x * (self.pixel_x + self.border)
            posy = self.start_y + dot_ofs + y * (self.pixel_y + self.border)
            self.fill_rect(posx, posy, dot_size, dot_size, color)


def main():
    print('EMPTY DAL implementation')
    display = DAL({"debug":True})
    cfg = display.configuration()


def test0():
    pass


if __name__ == "__main__":
    main()
    test0()
