# Test LED
import sys
import time
from machine import Pin
import genlib as gl

cfg = gl.get_board_config()
keys = cfg.keys()

if not 'LED' in keys:
    print(f'LED not correctly configured')
    sys.exit(1)
led = Pin(cfg['LED'], Pin.OUT)

print('LED should blink 10 times...')
try:
    for i in range(10):
        led.on()
        time.sleep(0.2)
        led.off()
        time.sleep(0.2)
finally:
    led.off()
