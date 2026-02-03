# Test BTN functionality

# Make sure we're on the right platform
import sys
import genlib as gl
if gl.platform != 'linux':
    print('This program/module was not written for this platform')
    sys.exit(1)

import time
from gpiozero import Button

cfg = gl.get_board_config()
hcfg = gl.get_config('hw.cfg')
cfg = cfg | hcfg
keys = cfg.keys()

if 'BTN' not in keys:
    print('BTN not correctly configured')
    sys.exit(1)

stop = False


def btn_isr(pin):
    global stop
    stop = True


btn = Button(cfg['BTN'])
btn.when_pressed = btn_isr
btn.hold_time = 0.1

print('Press the button (or Ctrl-C) to exit...')

try:
    while not stop:
        time.sleep(0.2)
except KeyboardInterrupt:
    pass
finally:
    btn.when_pressed = None

print('')
msg = '' if stop else 'not '
print(f'BTN ISR was {msg}detected')
