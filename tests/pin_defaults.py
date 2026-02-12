# Get default pin assignments for I2C and SPI communication

# This is very platform specific
import sys
import genlib as gl
if gl.platform == 'linux':
    print('This module was not written for this platform')
    sys.exit()

print()

cfg = gl.get_board_config()
debug = 'debug' in cfg and cfg['debug']

# Microcontroller micropython
from machine import I2C, SPI  # noqa E402
# Find valid I2C ports
port = 0
while True:
    try:
        i2c = I2C(port)
        if debug:
            print(f'i2c - {i2c}')
        si2c = str(i2c)
        if debug:
            print(f'str(i2c) - {si2c}')
        svals = si2c.split(' ')
        if debug:
            print(f'split(\' \') - {svals}')
        scl = -1
        sda = -1
        for val in svals:
            tmp = val.split('=')
            if debug:
                print(f'split(\'=\') - {tmp}')
            if tmp[0].startswith('scl'):
                scl = int(tmp[1][:-1])
            elif tmp[0].startswith('sda'):
                sda = int(tmp[1][:-1])
        if sda == -1:
            print(f'I2C port {port} - sda not found')
        if scl == -1:
            print(f'I2C port {port} - scl not found')
        if sda >= 0 and scl >= 0:
            print(f'I2C port #{port} default scl={scl}, sda={sda}')
        del i2c
        port += 1
    except ValueError:
        # sometimes ports are unavailable
        if port > 5:
            break
        port += 1

print()

# Find valid SPI ports
port = 0
while True:
    try:
        spi = SPI(port)
        if debug:
            print(f'spi - {spi}')
        sspi = str(spi)
        if debug:
            print(f'str(spi) - {sspi}')
        svals = sspi.split(' ')
        if debug:
            print(f'split(\' \') - {svals}')
        sck = -1
        mosi = -1
        miso = -1
        for val in svals:
            tmp = val.split('=')
            if debug:
                print(f'split(\'=\') - {tmp}')
            if tmp[0].startswith('sck'):
                sck = int(tmp[1][:-1])
            elif tmp[0].startswith('mosi'):
                mosi = int(tmp[1][:-1])
            elif tmp[0].startswith('miso'):
                miso = int(tmp[1][:-1])
        if miso == -1:
            print(f'SPI port {port} - miso not found')
        if mosi == -1:
            print(f'SPI port {port} - mosi not found')
        if sck == -1:
            print(f'SPI port {port} - sck not found')
        if sda >= 0 and scl >= 0:
            print(f'SPI port #{port} default sck={sck}, mosi={mosi}, miso={miso}')
        del spi
        port += 1
    except ValueError:
        # sometimes ports are unavailable
        if port > 5:
            break
        port += 1

print()
