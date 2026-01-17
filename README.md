BCD Clock MicroPython application
=================================

This application uses common display hardware, including SH1106,
SSD1306, ST7735 and ST7789 screens and WS2812 panels to display a simple
BCD clock. The application code was developed and tested on Raspberry Pi Pico 2W,
ESP32, ESP32 CAM, ESP32 S2 mini and ESP32 S3 microprocessors. It is largely platform
independent and should work on other MicroPython platforms that support the required
interface(s).

Installation
------------

- Copy the code and configuration files (lib/\*, src/\*, test/\*) to your microprocessor.
- Modify the lan.cfg file to define your local network ssid and password. Remove
the file to use the RTC without NTP updates to determine local time. The genlib
library expects the RTC to return UTC time. If you want to display the RTC time
directly, set the 'display_rtc' option in the bcd.clock.cfg file to true.
- If necessary, modify one of the platform specific configuration files (hw_{platform}.cfg)
according to your system.
- Copy the platform specific configuration file to hw.cfg
- If necessary, modify one of the display specific configuration files ({display}.cfg).
- Copy the display configuration file to display.cfg
- Run the corresponding display test program (test_{display}.py) to make sure the
configuration settings are correct.
- Run the bcd_clock application

Wiring
------
At least one of the platform specific configuration files must be copied to hw.cfg. You
can define new files for different platforms and/or system configurations. Only those
interface sections that are used need to be defined.

At least one of the display configuration files must be copied to display.cfg to activate
the display hardware and determine the value of any display specific options.
The default configuration files define all the values and options supported by the low
level device driver and DAL implementation.

The SH1106 and SSD1306 DAL drivers use a hardware or software based I2C bus to
communicate with the display. Currently, the SSD1306 driver does not support
display rotation.

The ST7735 and ST7789 DAL drivers use a hardware SPI bus to communicate with the
display.

ST7735 displays come in many flavors. There are multiple internal initialization
routines and options that need to be correct for error free display. If the display
generally works, but small border issues are visible, try modifying the offset
setting in the display configuration file. See the header of the dal_st7735.py
for more information.

The WS2812 driver is platform specific for the Raspberry Pi Pico microprocessot. It uses
a single GPIO pin to send data to the 2D LED panel. Since the Pico uses 3.3V logic levels, a
level shifter is necessary to correctly drive the data signal. With minor modifications, this
driver should work with any compatible 2D display. The Pico may not support the 5V current
drain necessary to drive your specific display panel correctly. If so, use an external 5V
power source. Running the application as is, my 16x16 panel typically draws about 240mA,
the 8x8 panel draws about 75mA. The default LED intensity is reduced significantly in the
base driver. The current can be further reduced by changing the frame color
from LTGRAY to VVLTGRAY (bcd\_clock.cfg).

The ESP32 CAM platform has very few free GPIO pins. Although it can work, it is not
recommended to use any display that requires an SPI interface (st7735/st7789). Note that
I used the generic ESP32 version of micropython. I did not test the special versions
that include camera support. If the LED and BTN are active, all displays use GPIO pins
that conflict with the internal SD card interface. The displays work, but the SD card
is no longer accessible.

If you are unsure about which pins to use to control your display, use the pins
as defined in the platform specific configuration files.

Here is a list of the default hardware connections used on the Raspberry PICO 2W;

LED (optional)<br>
GPIO 15

BTN (optional)<br>
GPIO 14

WS2812 (ws2812.cfg)<br>
GPIO 5 is used to send data to the panel (routed through a 3.3V/5V level converter)
An external power supply is used to provide 5V to the panel, although the 8x8 panel
can be powered from the microprocessor 5V VSYS pin. The neopixel module does not work
correctly on my microprocessors.

SSD1306 (ssd1306.cfg)<br>
SH1106 (sh1106.cfg)<br>
The following pins are used for the I2C bus (port 1);<br>
GPIO 18         I2C SDA<br>
GPIO 19         I2C SCL<br>

ST7735 (st7735.cfg)<br>
ST7789 (st7789.cfg)<br>
The following pins are used for the SPI bus (port 0)<br>
GPIO 18         SPI SCK  (SCL)<br>
GPIO 19         SPI MOSI (SDA)<br>
GPIO 16         SPI MISO (DC)<br>
GPIO 17         SPI CS   (CS)<br>
GPIO 21         SPI RST  (RES)<p>

and here are the default hardware connections used on the ESP32;

LED (optional)<br>
GPIO 5

BTN (optional)<br>
GPIO 12

neopixel (neopixel.cfg)<br>
GPIO 22 is used to send data to the panel (routed through a 3.3V/5V level converter)
An external power supply must be used to provide 5V to the panel. The ws2812 driver is
platform specific and can not be used on ESP systems. The MicroPython neopixel module
appears to be flaky (noisy DIN signal) on some platforms.

SSD1306 (ssd1306_esp.cfg)<br>
SH1106 (sh1106_esp.cfg)<br>
The following pins are used for the I2C bus (port 1);<br>
GPIO 18         I2C SDA<br>
GPIO 23         I2C SCL<br>

ST7735 (st7735_esp.cfg)<br>
ST7789 (st7789_esp.cfg)<br>
The following pins are used for the SPI bus (port 2)<br>
GPIO 18         SPI SCK  (SCL)<br>
GPIO 23         SPI MOSI (SDA)<br>
GPIO 19         SPI MISO (DC)<br>
GPIO 27         SPI CS   (CS)<br>
GPIO 15         SPI RST  (RES)<p>

Additional Information
----------------------
Development and tests were performed using the following versions of MicroPython;<br>
Raspberry Pi Pico 2W<br>
- MicroPython v1.27.0 on 2025-12-09; Raspberry Pi Pico 2 W with RP2350<br>
ESP32<br>
- MicroPython v1.27.0 on 2025-12-09; Generic ESP32 module with ESP32<br>
ESP32 S2 mini<br>
- MicroPython v1.27.0 on 2025-12-09; LOLIN_S2_MINI with ESP32-S2FN4R2<br>
ESP32 S3<br>
- MicroPython v1.27.0 on 2025-12-09; Generic ESP32S3 module with ESP32S3
ESP32 CAM<br>
- MicroPython v1.27.0 on 2025-12-09; Generic ESP32 module with ESP32<br>

Configuration options are stored in json files (\*.cfg). The top level
configuration is stored in board.cfg. This optional file contains global options
that are seldom modified. The optional application configuration file bcd_clock.py defines
application specific default options, this file is also usually unmodified. The
hardware configuration file hw.cfg contains platform specific hardware options as
well as display interface settings. The display.cfg file and the optional DAL
configuration dal\_{display}.cfg file contains display level options that are
usually not modified. Each configuration file is read in the above order
and can override settings defined at the previous level.

The display drivers have been modified to provide a relatively consistent
API for initialization and simple graphics functions. I did not write the
original display driver code. The initial author(s), if known, are documented
in the source code comments.

Some of the low level drivers do not support software or hardware rotation.
Many claim to support different physical display sizes. All my displays use
the default display sizes, geometry and color coding.

The display abstraction layer code supports all of the low level driver
options using the associated configuration files. All the configuration options
are documented in the file header. In the case of drivers that support both SPI
and I2C communication, I have used the I2C bus classes and have not tested SPI
communication with these devices. Modify the appropriate DAL implementation and
associated configuration file if you want to use the SPI interface.

The library files (notably genlib.py and lan.py) are intended to be platform
independent. The ws2812 driver is the only low level device driver that uses
Raspberry Pi specific code. Many of the low level drivers could be optimized
using appropriate @MicroPython decorators. I have tried to minimize the
modifications I made to the original drivers.

The genlib module defines various hardware independent functions I use often
in my application code. The automatic DST compensation is specific for Germany
but could be modified for other time zones. It has been tested and used on
Raspberry Pi 3b+, 4, Zero 2W, Pico 2, Pico 2W, ESP32, ESP32 S2 mini and ESP32
Cam platforms.

The lan module defines common network functions.

Any bug fixes or suggestions about improvements are welcome...

