# Test BTN
import sys
import time
from machine import Pin
import genlib as gl

cfg = gl.get_board_config()
keys = cfg.keys()

if not 'BTN' in keys:
    print(f'BTN not correctly configured')
    sys.exit(1)
    
stop = False
def btn_isr(pin):
    global stop
    time.sleep(0.1)
    if pin.value() == 0:
        stop = True

btn = Pin(cfg['BTN'], Pin.IN, Pin.PULL_UP)
btn.irq(handler=btn_isr, trigger=Pin.IRQ_FALLING)

print('Press the button (or Ctrl-C) to exit...', end='')

try:
    while not stop:
        time.sleep(0.2)
except KeyboardInterrupt:
    pass
finally:
    btn.irq(handler=None)

print('')
if stop:
    print('BTN ISR OK')
