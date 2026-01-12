# I2C scanner with hexadecimal and decimal address output
from machine import Pin, I2C, SoftI2C
import genlib as gl

print()

# Get board specific configuration
cfg = gl.get_board_config()
keys = cfg.keys()

if 'i2c_sda' not in keys:
    raise Exception('The I2C bus is not configured')
soft = 'i2c_soft' in keys and cfg['i2c_soft']
if not soft and 'i2c_port' not in keys:
    raise Exception('The I2C port is not configured')
if 'i2c_scl' not in keys:
    raise Exception('The I2C scl pin is not defined')
freq = 400_000
if 'i2c_freq' in keys:
    freq = int(cfg['i2c_freq'])
pscl = Pin(cfg['i2c_scl'], Pin.OUT, Pin.PULL_UP)
sda = cfg['i2c_sda']
psda = Pin(sda, Pin.OUT, Pin.PULL_UP)
if soft:
    i2c = SoftI2C(scl=pscl, sda=psda, freq=freq)
else:
    i2c = I2C(int(cfg['i2c_port']), scl=pscl, sda=psda, freq=freq)
if not i2c:
    raise Exception('I2C not correctly configured')

print(f'Scanning for I2C devices using {i2c}')

devices = i2c.scan()
dcnt = len(devices)
print('I2C Device', end='')
if dcnt < 1:
    print('s : None detected')
else:
    print('s : ' if dcnt > 1 else ' : ', end='')
    for dev in devices:
        print(f'0x{dev:02X}={dev} ', end='')
    print()
