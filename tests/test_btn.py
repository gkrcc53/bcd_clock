# Test BTN functionality

# Make sure we're on the right platform
try:
    import sys
    import genlib as gl
    if gl.platform == 'linux':
        print('This program was not written for this platform')
        sys.exit()

    import time
    from machine import Pin

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
    msg = '' if stop else 'not '
    print(f'BTN ISR was {msg}detected')
except SystemExit:
    pass
