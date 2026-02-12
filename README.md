BCD Clock MicroPython/Python application
========================================

This application uses common display hardware, including SH1106,
SSD1306, ST7735 and ST7789 screens and WS2812 panels to display a simple
BCD clock. The application code was developed and tested on Raspberry Pi Zero 2W,
Pico 2W, ESP32, ESP32 CAM, ESP32 S2 mini, ESP32 C3 mini, and ESP32 S3 mini/zero microprocessors. It is
largely platform independent and should work on other MicroPython and Python
platforms that support the required interface(s).

What's New
----------

- The code now supports the Raspberry Pi Zero microcomputer platform
- Support for additional microprocessor platforms has been added
- A simple text clock application is available
- The bcd_clock program switches between date and time display periodically
- All of the DAL implementations include test code<p>

Installation
------------

- Copy the code and configuration files (lib/\*, src/\*, tests/\*) to your microprocessor
or microcomputer. On most systems, the lib/\* files can be copied to the /lib
subdirectory on your microprocessor. On the Raspberry Pi Zero, I use a flat file
structure.
- Modify the lan.cfg file to define your local network ssid and password. Remove
the file to suppress NTP updates. The genlib
library expects the RTC to return UTC time. If the RTC time returns local time,
set the 'display_rtc' option in the bcd_clock.cfg file to true.
- If necessary, modify one of the platform specific configuration files (hw\_{platform}.cfg)
according to the wiring of your system.
- Copy the platform specific configuration file to hw.cfg
- If necessary, modify one of the display specific configuration files ({display}.cfg).
- Copy the display configuration file to display.cfg
- Run the display test program (test\_{display}.py) and/or the DAL implementation 
file (dal_{display}.py) to make sure the configuration settings are correct.
- Run the bcd_clock application

Wiring
------
At least one of the platform specific configuration files must be copied to hw.cfg. You
can define new files for different platforms and/or system configurations. Only those
interface sections that are used need to be defined.

At least one of the display configuration files must be copied to display.cfg to activate
the display hardware and determine the value of any display specific options.
The default configuration files define all the values and options supported by the low
level device driver and corresponding DAL implementation.

The SH1106 and SSD1306 DAL drivers use a hardware based I2C bus to
communicate with the display. Currently, the low level SSD1306 driver on
MicroPython systems does not support display rotation.

The ST7735 and ST7789 DAL drivers use a hardware SPI bus to communicate with the
display.

ST7735 displays come in many flavors. There are multiple internal initialization
routines and options that need to be correct for error free display. If the display
generally works, but small border issues are visible, try modifying the offset
setting in the display configuration file. See the header of the dal_st7735.py
for more information.

The WS2812 driver is platform specific for the Raspberry Pi Pico microprocessor. It uses
a single GPIO pin and a platform specific PIO routine to send data to the 2D LED panel.
Since all the tested microprocessors use 3.3V logic levels, a level shifter is necessary
to correctly drive the 5V data signal. With  minor modifications, this driver should work
with any compatible 2D display. The microprocessors may not support the 5V current
drain necessary to drive your specific display panel correctly. 
To make sure, always use an external 5V power source. Running the application as is,
my 16x16 panel typically draws about 240mA, the maximum current drain is more than 2A.
The 8x8 panel typically draws about 75mA, the maximum drain is 800mA on my system.
The default LED intensity is reduced 
significantly in the base driver. The typical current drain can be further reduced by
changing the frame color from LTGRAY to VVLTGRAY (bcd\_clock.cfg). The test programs 
and DAL implementations __main__ code drive the panels at maximum intensity to make
sure the power supply is sufficient. This can be suppressed by setting the 'test_power'
display configuration setting to false.

The ESP32 CAM platform has very few free GPIO pins. Although it does work, it is not
recommended to use any display that requires an SPI interface (st7735/st7789). Note that
I used the generic ESP32 version of MicroPython. I did not test the special versions
that include camera support. If the LED and BTN are active, all displays use GPIO pins
that conflict with the internal SD card interface. The displays do work, but the SD card
is no longer accessible.

If you are unsure about which pins to use to control your display, or if your pin
assignments do not work correctly, use the pins as defined in the default platform
specific configuration files.

Here is a list of the default hardware connections used on the Raspberry Pico 2W;

LED (optional)<br>
GPIO 14

BTN (optional)<br>
GPIO 15

WS2812 (ws2812.cfg)<br>
GPIO 5 is used to send data to the panel (routed through a 3.3V/5V level converter)
An external power supply is used to provide 5V to the panel, although the 8x8 panel
can be powered from the microprocessor 5V VSYS pin. The system neopixel module does
not work correctly on the Pico 2W.

SSD1306 (ssd1306.cfg)<br>
SH1106 (sh1106.cfg)<p>
The following pins are used for the I2C bus (port 1);<br>
GPIO 6         I2C SDA<br>
GPIO 7         I2C SCL<br>

ST7735 (st7735.cfg)<br>
ST7789 (st7789.cfg)<p>
The following pins are used for the SPI bus (port 0)<br>
GPIO 18         SPI SCK  (SCL)<br>
GPIO 19         SPI MOSI (SDA)<br>
GPIO 16         SPI MISO (DC)<br>
GPIO 17         SPI CS   (CS)<br>
GPIO 21         SPI RST  (RES)<p>

Additional Information
----------------------
Development and tests were performed using the following versions of MicroPython or Python;<p>
Raspberry Pi Pico 2W<br>
- MicroPython v1.27.0 on 2025-12-09; Raspberry Pi Pico 2 W with RP2350<br>
ESP32<br>
- MicroPython v1.27.0 on 2025-12-09; Generic ESP32 module with ESP32<br>
ESP32 S2 mini<br>
- MicroPython v1.27.0 on 2025-12-09; LOLIN_S2_MINI with ESP32-S2FN4R2<br>
ESP32 C3 mini<br>
- MicroPython v1.27.0 on 2025-12-09; Generic ESP32S3 module with ESP32S3<br>
ESP32 S3 mini<br>
- MicroPython v1.27.0 on 2025-12-09; Generic ESP32S3 module with ESP32S3<br>
ESP32 CAM<br>
- MicroPython v1.27.0 on 2025-12-09; Generic ESP32 module with ESP32<br>
Raspberry Pi Zero 2W<br>
- Python 3.13.5<p>

Configuration options are stored in json files (\*.cfg). The top level
configuration is stored in board.cfg. This optional file contains global options
that are seldom modified. The optional application configuration file bcd_clock.py defines
application specific default options, this file is also usually unmodified. The
hardware configuration file hw.cfg contains platform specific hardware options as
well as display interface settings. The display.cfg file and the optional DAL
configuration dal\_{display}.cfg file contain display level options that are
usually not modified. Each configuration file is read in the above order
and can override settings defined at the previous level.

The display drivers have been modified to provide a relatively consistent
API for initialization and simple graphics functions. I did not write the
original display driver code. The initial author(s), if known, are documented
in the source code comments.

Some of the low level drivers do not support software or hardware rotation.
Many claim to support different physical display sizes. All my displays use
the default display sizes, geometry, and color coding.

The display abstraction layer code supports all of the low level driver
options using the associated configuration files. All the configuration options
are documented in the file header. In the case of drivers that support both SPI
and I2C communication, I have used the I2C bus classes and have not tested SPI
communication with these devices. Modify the appropriate DAL implementation and
associated configuration file if you want to use the SPI interface.

Each DAL implementation contains test code that is executed if the module is
run as a program.

The library files (notably genlib.py, hal.py, and lan.py) are intended to be 
platform independent. The ws2812 driver is the only low level device driver that 
uses Raspberry Pi specific code. Many of the low level drivers could be optimized
using appropriate @MicroPython decorators. I have tried to minimize the
modifications I made to the original drivers.

The genlib module defines various hardware independent functions I use often
in my application code. The automatic DST compensation is specific for Germany
but could be modified for other time zones. It has been tested and used on
Raspberry Pi 3b+, 4, Zero 2W, Pico 2, Pico 2W, ESP32, ESP32 S2 mini, ESP32 S3
mini/zero and ESP32 Cam platforms.

The hal module is a small abstraction layer that supports MicroPython and Python
code to initialize and control common hardware.

The lan module defines common network functions for MicroPython.

The Raspberry Pi Zero 2W code requires activation of system
hardware and installation of system drivers. Please consult the separate documentation
in README_ZERO.md for more information.

Any bug fixes or suggestions about improvements are welcome...

