BCD Clock MicroPython application
=================================

BCD Clock application using common display hardware, including SH1106,
SSD1306, ST7735, ST7789, and WS2812 modules. The application code was
developed for and on a Raspberry Pi Pico 2W microprocessor.

Installation
------------

Copy the code and configuration files (\*.py, \*.cfg) to your microprocessor.

Modify the lan.cfg file to define your local network ssid and password. Remove
the file to use the RTC without NTP updates to determine local time. The genlib
library expects the RTC to return UTC time.

Modify one or more of the example display specific configuration files (\*.cfg)
and copy the file to board.cfg to activate your installed display hardware.

Wiring
------

The {display}.cfg files are used to activate the indicated display hardware, define
the GPIO Pin(s) used for hardware communication and determine the value of any
display specific configuration options. The default configuration files define all
initialization values supported by the low level device driver.

The SH1106 and SSD1306 DAL drivers use a hardware or software based I2C bus to
communicate with the display. Currently, the SSD1306 driver does not support
display rotation.

The ST7735 and ST7789 DAL drivers use a hardware SPI bus to communicate with the
display.

ST7735 displays come in many flavors. Modify the dal_st7735 file if your hardware
does not work correctly. There are multiple internal initx() routines and options
that need to be correct for error free display. If the display generally works,
but small border issues are visible, try modifying the offset value in the
configuration file.

The WS2812 driver uses a single GPIO pin to send data to the 2D LED panel.
Since the Raspberry Pi PICO 2W uses 3.3V logic levels, a level shifter is
necessary to correctly drive the DIN data signal. With minor modifications,
this driver should work with any size display. The microprocessor may not
support the 5V current drain necessary to drive your specific WS2812 2D
display panel correctly. If so, use an external 5V power source. Running the
application as is, my 16x16 panel typically draws about 220mA, the 8x8 panel
draws about 20mA. The default LED intensity is reduced significantly in the
base driver.

Additional Information
----------------------
The display drivers have been modified to provide a relatively consistent
API for initialization and simple graphics functions. I did not write the
original display driver code. The initial author(s), if known, are documented
in the source code comments.

Some of the low level drivers do not support software or hardware rotation.
Many claim to support different physical display sizes. All my displays use
the default display size, geometry and color coding.

The display abstraction layer code supports all of the low level driver
options using the associated configuration file. All the configuration options
are documented in the file header. In the case of drivers that support both SPI
and I2C communication, I have used the I2C bus classes and have not tested SPI
communication with these devices. Modify the appropriate DAL implementation and
associated configuration file if you want to use the SPI interface.

The library files (notably genlib.py and lan.py) are intended to be platform
independent. The ws2812 driver is the only low level device driver that uses
Raspberry Pi specific code. Many of the low level drivers could be optimized
using appropriate @micropython decorators. I have tried to minimize the
modifications I made to the original drivers.

The genlib module defines various hardware independent functions I use often
in my application code. The automatic DST compensation is specific for Germany
but could be modified for other time zones. It has been tested and used on
Raspberry Pi 3b+, 4, Zero 2W, Pico 2, Pico 2W, ESP32, ESP32 S2 mini and ESP32
Cam platforms.

The lan module defines common network functions.

Any bug fixes or suggestions about improvements are welcome...
