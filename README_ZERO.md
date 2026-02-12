Raspberry Pi Zero 2W Installation
=================================

The Raspberry Pi Zero 2W files should theoretically work on other Raspberry Pi based
microcomputers (perhaps with small modifications) but I have not done testing
on any other hardware.

<b>Low level device activation</b><p>

<b>I2C devices</b><br>
- Run raspi-config<br>
- Go to Interface Options/I2C<br>
- Activate the I2C interface<p>

I added the following line to the /boot/firmware/config.txt file to
set the I2C baudrate;<p>

dtparam=i2c_arm_baudrate=300000

Some of my display hardware did not work reliably at the 
documented baudrate of 400000. I understand that the default baudrate
is 100000.<p>

Your displays may not require any baudrate modification...<p>

<b>SPI devices</b><br>
- Run raspi-config<br>
- Go to Interface Options/SPI<br>
- Activate the SPI interface<p>

<b>Low level driver installation</b><p>

The MicroPython drivers will not work on the Raspberry Pi Zero. System
drivers need to be installed. Frequently, they are similar or identical
to the MicroPython drivers.<p>

To support the <b>NeoPixel</b> displays, the following commands were executed;<p>

sudo pip3 install rpi_ws281x adafruit-circuitpython-neopixel --break-system-packages<br>
sudo python3 -m pip install --force-reinstall adafruit-blinka --break-system-packages<p>

To support the <b>I2C</b> displays (sh1006, ssd1306), the following commands were
executed;<br>
- pip3 install luma-core luma-oled<br>
- pip3 install adafruit-circuitpython-rgb-display --break-system-packages<p>

To support the <b>SPI</b> displays (st7735, st7789), the following commands were
executed;<br>
- sudo apt install python3-pip python3-pil python3-dev python3-numpy python3-libgpiod<br>
- sudo pip3 install st7735 --break-system-packages<br>
- sudo pip3 install gpiod --break-system-packages<br>
- sudo pip3 install gpiodevice --break-system-packages<br>
- sudo apt install python3-opencv<p>

It is likely that some of the above modules are unnecessary...<p>

My ST7789 display requires "inverted" colors, which the default driver did
not support as an option. I modified the source code slightly to allow this
option, the modified file is in the zero subdirectory of the repository.<br>
On my system, the file
is stored under;<p>
~/.local/lib/python3.13/site-packages/adafruit_rgb_display

Your display(s) may not require this modified system driver.<p>
