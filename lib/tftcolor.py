# define device independent color handling routines and constants
# for RGB565 displays
#
# Interesting side-note: the green value is deeper because humans are more sensitive
# to shades of green than red or blue

# Convert a red, green and blue tuple or values (0-255) into a 16-bit 565 color value
def color565(red, green=0, blue=0):
    if isinstance(red, (tuple, list)):
        red, green, blue = red[:3]
    return (red & 0xF8) << 8 | (green & 0xFC) << 3 | (blue & 0xF8) >> 3

BLACK     = color565(0x00, 0x00, 0x00)
RED       = color565(0xFF, 0x00, 0x00)
LTRED     = color565(0x80, 0x00, 0x00)
GREEN     = color565(0x00, 0xFF, 0x00)
LTGREEN   = color565(0x00, 0x80, 0x00)
BLUE      = color565(0x00, 0x00, 0xFF)
LTBLUE    = color565(0x00, 0x00, 0x80)
CYAN      = color565(0x00, 0xFF, 0xFF)
LTCYAN    = color565(0x00, 0x80, 0x80)
MAGENTA   = color565(0xFF, 0x00, 0xFF)
LTMAGENTA = color565(0x80, 0x00, 0x80)
WHITE     = color565(0xFF, 0xFF, 0xFF)
GRAY      = color565(0x80, 0x80, 0x80)
YELLOW    = color565(0xFF, 0xFF, 0x00)
LTYELLOW  = color565(0x80, 0x80, 0x00)
LTGRAY    = color565(0x40, 0x40, 0x40)
VLTGRAY   = color565(0x20, 0x20, 0x20)
VVLTGRAY  = color565(0x10, 0x10, 0x10)
