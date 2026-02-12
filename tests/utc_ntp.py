# Update the RTC to UTC using local NTP server

# Make sure we're on the right platform
import sys
import genlib as gl
if gl.platform == 'linux':
    print('This program/module was not written for this platform')
    sys.exit(1)

lan = None

# Load standard hardware configuration files
cfg = gl.get_board_config()
cfg |= gl.get_config('hw.cfg')

try:
    if not gl.file_exists('lan.cfg'):
        print('lan module configuration is not available')
        sys.exit()
    cfg |= gl.get_config('lan.cfg')
    from time import sleep
    from lan import LAN
    lan = LAN()
    lan.debug = 'debug' in cfg and cfg['debug']
    if lan.connect():
        print(f'Connected to {cfg["ssid"]}')
        txp = lan.wlan.config('txpower')
        if 'txpower' in cfg:
            val = cfg['txpower']
            if val != -1 and val != txp:
                lan.wlan.config(txpower=val)
            txp = lan.wlan.config('txpower')
        print(f'Maximum transmit power is {txp} dBm')
        sleep(1)
        lan.update_rtc()
        print('RTC updated')
    else:
        print('LAN connection failed')
except SystemExit:
    pass
except KeyboardInterrupt:
    pass
finally:
    if lan is not None:
        lan.disconnect()
