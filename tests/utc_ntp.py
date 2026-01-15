# Update the RTC to UTC using local NTP server
from time import sleep
from lan import LAN
lan = LAN()
#lan.debug = True
if lan.connect():
    print(f'Connected to {lan.config()["ssid"]}')
    sleep(1)
    lan.update_rtc()
    print('RTC updated')
    sleep(1)
    lan.disconnect()
else:
    print('LAN connection failed')
