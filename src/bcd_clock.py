# bcd clock application using display abstraction layer
#
# Configuration options
#   debug         - output debug information
#   verbose       - if debug, output copious information
#   lan_update    - use LAN to update RTC, default True
#   display_rtc   - if true, output RTC time directly,
#                   else RTC=UTC use genlib for DST compensation
#   show_digits   - call show() after each digit, False if not defined
#   bkg_color     - color of background pixels, else "black"
#   frame_color   - color of frame pixels, else "ltgray"
#   colon_color   - color of blinking colons, else "vltgray"
#   hour_color    - color of hour/day digits, else "red"
#   min_color     - color of minute/month digits, else "green"
#   sec_color     - color of second/year digits, else "blue"
#   time_interval - seconds to display time
#   date_interval - seconds to display date
#
# Notes
#   color options are;
#     "red", "ltred", "green", "ltgreen", "blue", "ltblue"
#     "cyan", "ltcyan", "magenta", ltmagenta", "yellow", "ltyellow",
#     "black", "white", "gray", "ltgray", "vltgray", vvltgray"

import time
import gc
import genlib as gl
from hal import HAL

print()

# Get optional board configuration
cfg = gl.get_board_config()

# Merge application configuration
appcfg = 'bcd_clock.cfg'
if not gl.file_exists(appcfg):
    raise Exception(f'Application configuration file {appcfg} not found')
pcfg = gl.get_config(appcfg)
cfg |= pcfg

# Get hardware abstraction layer
hal = HAL()

# Merge hardware configuration
hwcfg = 'hw.cfg'
if not gl.file_exists(hwcfg):
    raise Exception(f'Hardware configuration file {hwcfg} not found')
hcfg = gl.get_config(hwcfg)
cfg |= hcfg

# Merge display configuration
dscfg = 'display.cfg'
if not gl.file_exists(dscfg):
    raise Exception(f'Display configuration file {dscfg} not found')
dcfg = gl.get_config(dscfg)
cfg |= dcfg

# Get list of merged configuration keys
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
led = None
if 'LED' in keys:
    led = hal.get_led(cfg['LED'])
    led.off()

# use LED to show initialization progress
_blink_cnt = 1


def blink():
    global led, _blink_cnt
    if led is not None:
        cnt = _blink_cnt
        while cnt > 0:
            led.on()
            time.sleep(0.2)
            led.off()
            time.sleep(0.2)
            cnt -= 1
        _blink_cnt += 1


# Optional button to stop program cleanly
stop = False


def btn_isr(pin):
    global stop, hal
    if hal.iolib == 'machine':
        time.sleep(0.05)
        if pin.value() != 0:
            return
    stop = True


btn = None
if 'BTN' in keys:
    btn = hal.get_button(cfg['BTN'], pin_isr=btn_isr)

# Get DAL module name
if 'display_type' not in keys:
    raise Exception('Display type not configured')
dal_module = f'dal_{cfg["display_type"]}'

# DAL module may load large font file, optimize success
gc.collect()
if debug:
    print(f'Free memory: {gl.niceSize(gc.mem_free())}')

# Initialize display, module may load local configuration
display = __import__(dal_module).DAL(cfg)
if debug:
    print('Display initialized')
blink()

# Get display colors from DAL class
colors = {
    "black": display.BLACK,
    "red": display.RED,
    "ltred": display.LTRED,
    "green": display.GREEN,
    "ltgreen": display.LTGREEN,
    "blue": display.BLUE,
    "ltblue": display.LTBLUE,
    "cyan" : display.CYAN,
    "ltcyan": display.LTCYAN,
    "magenta": display.MAGENTA,
    "ltmagenta": display.LTMAGENTA,
    "yellow": display.YELLOW,
    "ltyellow": display.LTYELLOW,
    "white": display.WHITE,
    "gray": display.GRAY,
    "ltgray": display.LTGRAY,
    "vltgray": display.VLTGRAY,
    "vvltgray": display.VVLTGRAY}

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
if debug:
    print(f'display geometry:\n{dal_cfg}')
start_x = dal_cfg['start_x']
start_y = dal_cfg['start_y']
pixel_x = dal_cfg['pixel_x']
pixel_y = dal_cfg['pixel_x']
border = dal_cfg['border']
size = display.size

# Need at least 8x4 pixels
if size[0] < 8 or size[1] < 4:
    raise Exception('Minimum display size is 8x4 pixels')

# Options for time/date switching
time_interval = 15
if 'time_interval' in keys:
    time_interval = cfg['time_interval']

date_interval = 5
if 'date_interval' in keys:
    date_interval = cfg['date_interval']

# Optional LAN connection to update RTC periodically
lan_update = True
if 'lan_update' in keys:
    lan_update = cfg['lan_update']

# Get rid of some data we no longer need
del colors
del keys

# Seems to help sometimes...
gc.collect()

if debug:
    print(f'Free memory : {gc.mem_free()}')

lan = None
if lan_update:
    lan = hal.get_lan()
    if lan is not None:
        blink()

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


def blink_colon():
    global dots_on, bcolor, ccolor
    tmp_color = ccolor if dots_on else bcolor
    display.dot_set(2, 1, tmp_color)
    display.dot_set(2, 2, tmp_color)
    display.dot_set(5, 1, tmp_color)
    display.dot_set(5, 2, tmp_color)
    dots_on = not dots_on


def show_dots():
    global bcolor, ccolor

    display.dot_set(2, 3, ccolor)
    display.dot_set(5, 3, ccolor)


# Display 2 digit year - decimal 0..99 BCD [0..9 0..9]
last_year = -1


def update_year(val):
    global last_year, scolor, bcolor
    if val == last_year:
        return

    last_year = val
    val %= 100

    # Clear year pixels
    display.xy_set(6, 0, bcolor)
    display.xy_set(6, 1, bcolor)
    display.xy_set(6, 2, bcolor)
    display.xy_set(6, 3, bcolor)
    display.xy_set(7, 0, bcolor)
    display.xy_set(7, 1, bcolor)
    display.xy_set(7, 2, bcolor)
    display.xy_set(7, 3, bcolor)

    # Display tens digit (0..9)
    save = val
    val = val // 10
    val = val % 10
    if val & 8 != 0:
        display.xy_set(6, 0, scolor)
    if val & 4 != 0:
        display.xy_set(6, 1, scolor)
    if val & 2 != 0:
        display.xy_set(6, 2, scolor)
    if val & 1 != 0:
        display.xy_set(6, 3, scolor)

    # Display ones digit (0..9)
    val = save
    val = val % 10
    if val & 8 != 0:
        display.xy_set(7, 0, scolor)
    if val & 4 != 0:
        display.xy_set(7, 1, scolor)
    if val & 2 != 0:
        display.xy_set(7, 2, scolor)
    if val & 1 != 0:
        display.xy_set(7, 3, scolor)


# Display 2 digit month - decimal 1..12 BCD [0..1 0..9]
last_month = -1


def update_month(val):
    global last_month, mcolor, bcolor
    if last_month == val:
        return

    last_month = val
    val = min(12, max(1, val))

    # Clear month pixels
    display.xy_set(3, 3, bcolor)
    display.xy_set(4, 0, bcolor)
    display.xy_set(4, 1, bcolor)
    display.xy_set(4, 2, bcolor)
    display.xy_set(4, 3, bcolor)

    # Display tens digit (0..1)
    if val > 9:
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


# Display 2 digit day - decimal 0..31 BCD [0..3 0..9]
last_day = -1


def update_day(val):
    global last_day, hcolor, bcolor
    if last_day == val:
        return

    last_day = val
    val = min(31, max(1, val))

    # Clear day pixels
    display.xy_set(0, 2, bcolor)
    display.xy_set(0, 3, bcolor)
    display.xy_set(1, 0, bcolor)
    display.xy_set(1, 1, bcolor)
    display.xy_set(1, 2, bcolor)
    display.xy_set(1, 3, bcolor)

    # Display tens digit (0..3)
    if val > 29 != 0:
        display.xy_set(0, 2, hcolor)
        display.xy_set(0, 3, hcolor)
    elif val > 19 != 0:
        display.xy_set(0, 2, hcolor)
    elif val > 9 != 0:
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

    show_dots()


# Display 2 digit hour - decimal 0..23 BCD [0..2 0..9]
# If you want AM/PM, add it yourself ;-)
last_hour = -1


def update_hours(val):
    global last_hour, hcolor, bcolor
    if val == last_hour:
        return

    val = min(23, max(0, val))
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

    val = min(59, max(0, val))
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

    val = min(59, max(0, val))
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

    blink_colon()


# Force all digits to be displayed
def force_show():
    global last_year, last_month, last_day
    global last_hour, last_min, last_sec

    last_year = last_month = last_day = -1
    last_hour = last_min = last_sec = -1


# Display test for graphics fine-tuning
def date_test():
    force_show()
    display.fill(bcolor)
    draw_frame()
    for i in range(26, 51):
        update_year(2000 + i)
        display.show()
        time.sleep(1)
    for i in range(1, 13):
        update_month(i)
        display.show()
        time.sleep(1)
    for i in range(1, 32):
        update_day(i)
        display.show()
        time.sleep(1)
    update_day(12)
    display_show()


# Display test for graphics fine-tuning
def time_test():
    global dots_on

    force_show()
    dots_on = True
    display.fill(bcolor)
    draw_frame()
    for i in range(0, 24):
        update_hours(i)
        display.show()
        time.sleep(1)
    for i in range(0, 60):
        update_minutes(i)
        display.show()
        time.sleep(1)
    for i in range(0, 60):
        update_seconds(i)
        display.show()
        time.sleep(1)


# Clear display from REPL
def clear():
    display.clear()


# Get the time and update the display
def update_time():
    global show_time

    if show_time:
        if display_rtc:
            lt = hal.get_time_direct()
            # Display the local time directly
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
    else:
        if display_rtc:
            lt = hal.get_time_direct()
        else:
            lt = gl.localtime()
        update_day(lt[2])
        if show_digits:
            display.show()
        update_month(lt[1])
        if show_digits:
            display.show()
        update_year(lt[0])
    display.show()


# main loop sleep time (seconds)
loop_delay = 0.1

# Set up time/date switching
time_counter = time_interval / loop_delay
if time_counter <= 0:
    time_counter = 0

date_counter = date_interval / loop_delay
if date_counter < 0:
    date_counter = 0

if date_counter == 0 and time_counter == 0:
    raise Exception('Both time and date are not displayed, I quit')

show_time = time_counter > 0

# update RTC periodically (seconds)
rtc_interval = 60 * 60
rtc_counter = rtc_interval / loop_delay

# do periodic garbage collection (seconds)
collect_interval = 300
collect_counter = collect_interval / loop_delay

# Program loop
if debug:
    print('Starting clock loop')

try:
    display.fill(bcolor, show=True)
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
        if show_time:
            if date_counter > 0 and loop_cnt % time_counter == 0:
                show_time = False
                force_show()
                display.fill(bcolor, show=True)
                time.sleep(0.5)
                draw_frame()
        else:
            if time_counter > 0 and loop_cnt % date_counter == 0:
                show_time = True
                force_show()
                display.fill(bcolor, show=True)
                time.sleep(0.5)
                draw_frame()
        update_time()
        time.sleep(loop_delay)
except KeyboardInterrupt:
    pass
finally:
    if led is not None:
        led.off()
    if btn is not None:
        hal.disable_button_isr(btn)
    if lan is not None:
        lan.disconnect()
    display.clear()

print('Done')
