# Test LED

led = None

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

    if 'LED' not in keys:
        print('LED not correctly configured')
        sys.exit(1)
    led = Pin(cfg['LED'], Pin.OUT)

    print('LED should blink 10 times...')
    try:
        for i in range(10):
            led.on()
            time.sleep(0.2)
            led.off()
            time.sleep(0.2)
    except KeyboardInterrupt:
        pass
except SystemExit:
    pass
finally:
    if led is not None:
        led.off()
