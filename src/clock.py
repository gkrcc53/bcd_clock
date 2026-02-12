# Draw a simple date/time clock on the display
import sys
import time
import genlib as gl
from hal import HAL

print()

# Get platform configuration
cfg = gl.get_board_config()
cfg |= gl.get_config('hw.cfg')
cfg |= gl.get_config('display.cfg')
keys = cfg.keys()

debug = 'debug' in keys and cfg['debug']

hal = HAL()

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

display = None

# Suppress reset on exit
try:
    # Get DAL implementation
    if 'display_type' not in keys:
        print('Display type not configured')
        sys.exit()
    dal_module = f'dal_{cfg["display_type"]}'
    if not gl.module_available(dal_module):
        print(f'DAL implementation {dal_module} not available')
        sys.exit()

    # Initialize display
    display = __import__(dal_module).DAL(cfg)

    # Make sure display is available and supports simple text
    if display is None:
        print('Error initializing display')
        sys.exit()

    dcfg = display.configuration()

    if 'text' not in dcfg:
        print('Display device does not support simple text output')
        sys.exit()

    width = display.size[0]
    height = display.size[1]
    tsize = display.text_box('00:00:00')
    if debug:
        print(f'Font info : {tsize}')
    opaque = 'opaque_text' in dcfg and dcfg['opaque_text']

    x_size = tsize[2]
    y_size = tsize[3]
    x_pos = int((width - x_size) / 2) - tsize[0]
    y_pos = int((height - y_size) / 2) - tsize[1]
    if debug:
        print(f'Text info : [{x_pos}, {y_pos}, {x_size}, {y_size}]')
    show_time = True
    time_delay = 15000
    date_delay = 5000

    tstart = gl.local_ticks_ms()
    while not stop:
        switch = False
        if show_time:
            if gl.local_ticks_diff(gl.local_ticks_ms(), tstart) >= time_delay:  # noqa: E501
                show_time = False
                switch = True
            tstr = gl.strTime()
        else:
            if gl.local_ticks_diff(gl.local_ticks_ms(), tstart) >= date_delay:  # noqa: E501
                show_time = True
                switch = True
            tstr = gl.strDate(short=True)
        if not opaque:
            display.fill_rect(x_pos, y_pos, x_size, y_size, color=display.BLACK, show=False)
        display.text(tstr, x_pos, y_pos, color=display.WHITE)
        display.show()
        time.sleep(0.25)
        if switch:
            display.fill_rect(x_pos, y_pos, x_size, y_size, color=display.BLACK, show=True)
            time.sleep(0.5)
            tstart = gl.local_ticks_ms()
except SystemExit:
    pass
except KeyboardInterrupt:
    pass
finally:
    if display is not None:
        display.clear()
