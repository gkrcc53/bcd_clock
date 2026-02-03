# Update the RTC to UTC using local NTP server

# Make sure we're on the right platform
import sys
import genlib as gl
if gl.platform == 'linux':
    print('This program/module was not written for this platform')
    sys.exit(1)

lan = None

try:
    if not gl.file_exists('lan.cfg'):
        print('lan module configuration is not available')
        sys.exit()
    from time import sleep
    from lan import LAN
    lan = LAN()
    # lan.debug = True
    if lan.connect():
        print(f'Connected to {lan.config()["ssid"]}')
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
