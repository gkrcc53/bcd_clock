# Test LED

# Make sure we're on the right platform
import sys
import genlib as gl
if gl.platform != 'linux':
    print('This program/module was not written for this platform')
    sys.exit(1)

import time
from gpiozero import LED

cfg = gl.get_board_config()
hcfg = gl.get_config('hw.cfg')
cfg = cfg | hcfg
keys = cfg.keys()

if 'LED' not in keys:
    print('LED not correctly configured')
    sys.exit(1)
led = LED(cfg['LED'])

print('LED should blink 10 times...')
try:
    for i in range(10):
        led.on()
        time.sleep(0.2)
        led.off()
        time.sleep(0.2)
finally:
    led.off()
