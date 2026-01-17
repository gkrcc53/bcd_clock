# bcd clock application using display abstraction layer
#
# Configuration options
#   debug       - output debug information
#   verbose     - if debug, output copious information
#   display_rtc - if true, output RTC time directly, else RTC=UTC use genlib for DST compensation
#   show_digits - call show() after each digit, False if not defined
#   bkg_color   - color of background pixels, else "black"
#   frame_color - color of frame pixels, else "ltgray"
#   colon_color - color of blinking colons, else "vltgray"
#   hour_color  - color of hour digits, else "red"
#   min_color   - color of minute digits, else "green"
#   sec_color   - color of second digits, else "blue"
#
# Notes
#   color options are;
#     "red", "ltred", "green", "ltgreen", "blue", "ltblue"
#     "cyan", "ltcyan", "magenta", ltmagenta", "yellow", "ltyellow",
#     "black", "white", "gray", "ltgray", "vltgray", vvltgray"
    
import sys
import time
from machine import RTC, Pin
import gc
import genlib as gl

print()

# Get optional platform configuration
cfg = gl.get_board_config()

# Merge hardware configuration
if not gl.file_exists('hw.cfg'):
    print('Platform interfaces not configured')
    sys.exit(1)
hcfg = gl.get_config('hw.cfg')
cfg |= hcfg

# Merge optional application configuration
pcfg = gl.get_config('bcd_clock.cfg')
cfg = cfg | pcfg

# Merge display configuration
if not gl.file_exists('display.cfg'):
    print('Display not configured')
    sys.exit(1)
dcfg = gl.get_config('display.cfg')
cfg |= dcfg

# Get list of configuration keys
keys = cfg.keys()

# Get DAL module name
if 'display_type' not in keys:
    print('Display type not configured')
    sys.exit(1)
dal_module = f'dal_{cfg["display_type"]}'
if not gl.module_available(dal_module):
    print(f'DAL implementation {dal_module} not available')
    sys.exit(1)

# Optional DAL configuration overrides other settings
dalcfg = f'{dal_module}.cfg'
if gl.file_exists(dalcfg):
    dcfg = gl.get_config(dalcfg)
    cfg = cfg | dcfg
    keys = cfg.keys()

# Evaluate debug options first
debug = 'debug' in cfg and cfg['debug']
verbose = False
if debug:
    verbose = 'verbose' in cfg and cfg['verbose']
    for key in sorted(keys):
        print(f'{key:25}{cfg[key]}')
    print()

# Evaluate other program options
display_rtc = 'display_rtc' in keys and cfg['display_rtc']

show_digits = False
if 'show_digits' in keys:
    show_digits = cfg['show_digits']

# Initialize common hardware
# Optional LED to show activity
blink_cnt = 1
def blink():
    global led, blink_cnt
    if led is not None:
        cnt = blink_cnt
        while cnt > 0:
            led.on()
            time.sleep(0.2)
            led.off()
            time.sleep(0.2)
            cnt -= 1
        blink_cnt += 1

led = None
if 'LED' in keys and cfg['LED'] != -1:
    led = Pin(cfg['LED'], Pin.OUT)
    led.off()

# Optional button to stop program cleanly
stop = False
def btn_isr(pin):
    global stop
    time.sleep(0.05)
    if pin.value() == 0:
        stop = True

btn = None
if 'BTN' in keys and cfg['BTN'] != -1:
    btn = Pin(cfg['BTN'], Pin.IN, Pin.PULL_UP)
    btn.irq(handler=btn_isr, trigger=Pin.IRQ_FALLING)

# Seems to help sometimes...
gc.collect()

# Initialize display
display = __import__(dal_module).DAL(cfg)
if debug:
    print('Display initialized')

# Get display colors from DAL class
colors = {
    "black"     : display.BLACK,
    "red"       : display.RED,
    "ltred"     : display.LTRED,
    "green"     : display.GREEN,
    "ltgreen"   : display.LTGREEN,
    "blue"      : display.BLUE,
    "ltblue"    : display.LTBLUE,
    "cyan"      : display.CYAN,
    "ltcyan"    : display.LTCYAN,
    "magenta"   : display.MAGENTA,
    "ltmagenta" : display.LTMAGENTA,
    "yellow"    : display.YELLOW,
    "ltyellow"  : display.LTYELLOW,
    "white"     : display.WHITE,
    "gray"      : display.GRAY,
    "ltgray"    : display.LTGRAY,
    "vltgray"   : display.VLTGRAY,
    "vvltgray"  : display.VVLTGRAY}

# Set display colors from configuration
ckeys = colors.keys()

# Background color
bcolor = display.BLACK
if 'bkg_color' in keys:
    temp = cfg['bkg_color']
    if temp in ckeys:
        bcolor = colors[temp]

# Frame color
fcolor = display.LTGRAY
if 'frame_color' in keys:
    temp = cfg['frame_color']
    if temp in ckeys:
        fcolor = colors[temp]

# Colon color
ccolor = display.VLTGRAY
if 'colon_color' in keys:
    temp = cfg['colon_color']
    if temp in ckeys:
        ccolor = colors[temp]

# Hour color
hcolor = display.RED
if 'hour_color' in keys:
    temp = cfg['hour_color']
    if temp in ckeys:
        hcolor = colors[temp]

# Min color
mcolor = display.GREEN
if 'min_color' in keys:
    temp = cfg['min_color']
    if temp in ckeys:
        mcolor = colors[temp]

# Sec color
scolor = display.BLUE
if 'sec_color' in keys:
    temp = cfg['sec_color']
    if temp in ckeys:
        scolor = colors[temp]

# Get local copy of display geometry
dal_cfg = display.configuration()
start_x = dal_cfg['start_x']
start_y = dal_cfg['start_y']
pixel_x = dal_cfg['pixel_x']
pixel_y = dal_cfg['pixel_x']
border = dal_cfg['border']
size = display.size

# Display initialization complete
blink()

# Optional LAN connection to update RTC periodically
# Only import network library if required
lan = None
if gl.file_exists('lan.cfg'):
    from lan import LAN
    lan = LAN()
    if debug:
        print('Connecting to LAN')
    if not lan.connect():
        print('LAN connection failed')
        sys.exit(1)
    if debug:
        print('Updating local time')
    if not lan.update_rtc():
        print('RTC update failed')
        exit(1)

# update the display screen with a bcd representation of the time
# minimum geometric requirement 8 * 4 'virtual' pixels (6 digits + 2 colons)

# Display clock frame to make BCD visual interpretation easier
def draw_frame():
    global display
    global fcolor
    global start_x, start_y
    global pixel_x, pixel_y
    global size
    
    if border == 0:
        y0 = start_y - 1
        if y0 >= 0:
            display.hline(0, y0, size[0], fcolor)
            y0 = start_y + 4 * pixel_y
            display.hline(0, y0, size[0], fcolor)
    else:
        x0 = start_x - 2 * border
        y0 = start_y - 2 * border
        if y0 >= 0:
            # if y0 ok, then y1 must also be ok
            # Fix x0/x1 to allow horizontal lines to be drawn if possible
            if x0 < 0:
                x0 = 0
            x1 = start_x + 8 * (pixel_x + border) + 1
            if x1 > size[0]:
                x1 = size[0]
            lenx = x1 - x0
            y1 = start_y + 4 * (pixel_y + border) + 1
            leny = y1 - y0
            display.hline(x0, y0, lenx, fcolor)
            display.hline(x0, y1, lenx, fcolor)
            display.vline(x0, y0, leny, fcolor)
            display.vline(x1, y0, leny, fcolor)
        
# Display blinking colon to separate time fields
dots_on = True
def blink_dots():
    global dots_on, bcolor, ccolor

    tmp_color = ccolor if dots_on else bcolor
    display.dot_set(2, 1, tmp_color)
    display.dot_set(2, 2, tmp_color)
    display.dot_set(5, 1, tmp_color)
    display.dot_set(5, 2, tmp_color)
    dots_on = not dots_on

# Display 2 digit hour - decimal 0..23 BCD [0..2 0..9]
# If you want AM/PM, add it yourself ;-)
last_hour = -1
def update_hours(val):
    global last_hour, hcolor, bcolor
    if val == last_hour:
        return
    last_hour = val
    
    # Clear hour pixels
    display.xy_set(0, 2, bcolor)
    display.xy_set(0, 3, bcolor)
    display.xy_set(1, 0, bcolor)
    display.xy_set(1, 1, bcolor)
    display.xy_set(1, 2, bcolor)
    display.xy_set(1, 3, bcolor)

    # Display tens digit (0..2)
    if val > 19:
        display.xy_set(0, 2, hcolor)
    elif val > 9:
        display.xy_set(0, 3, hcolor)

    # Display ones digit (0..9)
    val = val % 10
    if val & 8 != 0:
        display.xy_set(1, 0, hcolor)
    if val & 4 != 0:
        display.xy_set(1, 1, hcolor)
    if val & 2 != 0:
        display.xy_set(1, 2, hcolor)
    if val & 1 != 0:
        display.xy_set(1, 3, hcolor)

# Display 2 digit minute - decimal 0..59 BCD [0..5 0..9]
last_min = -1
def update_minutes(val):
    global last_min, mcolor, bcolor
    if last_min == val:
        return
    last_min = val

    # Clear minute pixels
    display.xy_set(3, 1, bcolor)
    display.xy_set(3, 2, bcolor)
    display.xy_set(3, 3, bcolor)
    display.xy_set(4, 0, bcolor)
    display.xy_set(4, 1, bcolor)
    display.xy_set(4, 2, bcolor)
    display.xy_set(4, 3, bcolor)

    # Display tens digit (0..5)
    if val > 49 != 0:
        display.xy_set(3, 1, mcolor)
        display.xy_set(3, 3, mcolor)
    elif val > 39 != 0:
        display.xy_set(3, 1, mcolor)
    elif val > 29 != 0:
        display.xy_set(3, 2, mcolor)
        display.xy_set(3, 3, mcolor)
    elif val > 19 != 0:
        display.xy_set(3, 2, mcolor)
    elif val > 9 != 0:
        display.xy_set(3, 3, mcolor)

    # Display ones digit (0..9)
    val = val % 10
    if val & 8 != 0:
        display.xy_set(4, 0, mcolor)
    if val & 4 != 0:
        display.xy_set(4, 1, mcolor)
    if val & 2 != 0:
        display.xy_set(4, 2, mcolor)
    if val & 1 != 0:
        display.xy_set(4, 3, mcolor)

# Display 2 digit second - decimal 0..59 BCD [0..5 0..9]
last_sec = -1
def update_seconds(val):
    global last_sec, scolor, bcolor
    if last_sec == val:
        return
    last_sec = val

    # Clear second pixels
    display.xy_set(6, 1, bcolor)
    display.xy_set(6, 2, bcolor)
    display.xy_set(6, 3, bcolor)
    display.xy_set(7, 0, bcolor)
    display.xy_set(7, 1, bcolor)
    display.xy_set(7, 2, bcolor)
    display.xy_set(7, 3, bcolor)

    # Display tens digit (0..5)
    if val > 49 != 0:
        display.xy_set(6, 1, scolor)
        display.xy_set(6, 3, scolor)
    elif val > 39 != 0:
        display.xy_set(6, 1, scolor)
    elif val > 29 != 0:
        display.xy_set(6, 2, scolor)
        display.xy_set(6, 3, scolor)
    elif val > 19 != 0:
        display.xy_set(6, 2, scolor)
    elif val > 9 != 0:
        display.xy_set(6, 3, scolor)

    # Display ones digit (0..9)
    val = val % 10
    if val & 8 != 0:
        display.xy_set(7, 0, scolor)
    if val & 4 != 0:
        display.xy_set(7, 1, scolor)
    if val & 2 != 0:
        display.xy_set(7, 2, scolor)
    if val & 1 != 0:
        display.xy_set(7, 3, scolor)

    blink_dots()

# Display test for graphics fine-tuning
def test():
    global last_hour, last_min, last_sec, dots_on
    last_hour = last_min = last_sec = -1
    dots_on = True
    display.fill(bcolor)
    draw_frame()
    update_hours(23)
    if show_digits:
        display.show()
    update_minutes(59)
    if show_digits:
        display.show()
    update_seconds(59)
    display.show()

# Clear display from REPL
def clear():
    display.clear()

# Get the time and update the display
def update_time():
    if display_rtc:
        # Display the RTC time directly
        lt = RTC().datetime()
        hours = lt[4]
        mins = lt[5]
        secs = lt[6]
    else:
        # Assume RTC time is UTC, get local time using genlib
        lt = gl.localtime()
        hours = lt[3]
        mins = lt[4]
        secs = lt[5]
    update_hours(hours)
    if show_digits:
        display.show()
    update_minutes(mins)
    if show_digits:
        display.show()
    update_seconds(secs)
    display.show()

# main loop sleep time (seconds)
loop_delay = 0.1

# update RTC periodically (seconds)
rtc_interval = 60 * 60
rtc_counter = rtc_interval / loop_delay

# do periodic garbage collection (seconds)
collect_interval = 300
collect_counter = collect_interval / loop_delay

# Program loop
if debug:
    print('Starting clock loop')
    
# Main loop started
blink()

try:
    display.fill(bcolor)
    draw_frame()
    loop_cnt = 0
    while not stop:
        loop_cnt += 1
        if loop_cnt % rtc_counter == 0:
            if debug:
                print('Updating RTC')
            if lan is not None and not lan.update_rtc():
                print('RTC update failed')
        if loop_cnt % collect_counter == 0:
            if debug:
                print('Garbage collection')
            gc.collect()
        update_time()
        time.sleep(loop_delay)
except KeyboardInterrupt:
    pass
finally:
    if led is not None:
        led.off()
    if btn is not None:
        btn.irq(handler=None)
    if lan is not None:
        lan.disconnect()
    display.clear()

print('Done')
