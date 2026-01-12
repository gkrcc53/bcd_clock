# platform independent library to perform common functions
import json
import random
import sys
import os
import time

# local debug switch
_debug = False

# seconds since 00:00:00 on 01.01.2000
e2000_ms = 0

# global platform and board variable
_UNDEFINED = 'undefined'
board = _UNDEFINED
platform = None

# global cryptography variables
get_cipher = None
_MODE_ECB = 0
_BLOCK_SIZE = 16

# platform independent CPU temperature function
get_cpu_temperature = None

# UTC Epoch ranges in which DST correction should be applied
# ranges for 2021 up until and including 2037 (DE only)
dst_ranges =[(1616893200, 1635645600), (1648342800, 1667095200), (1679792400, 1698544800), 
             (1711846800, 1729994400), (1743296400, 1761444000), (1774746000, 1792893600), 
             (1806195600, 1824948000), (1837645200, 1856397600), (1869094800, 1887847200), 
             (1901149200, 1919296800), (1932598800, 1950746400), (1964048400, 1982800800), 
             (1995498000, 2014250400), (2026947600, 2045700000), (2058397200, 2077149600), 
             (2090451600, 2108599200), (2121901200, 2140048800)]

# Is the indicated module available
def module_available(name):
    try:
        __import__(name)
        return True
    except ImportError:
        return False

# Pad a bytearray to a valid multiple of _BLOCK_SIZE bytes
def pad_data(data : bytearray) -> bytearray:
    pad = _BLOCK_SIZE - len(data) % _BLOCK_SIZE
    bpad = b'\0' * pad
    return data + bpad
    
# Convert a string to a bytearray padded to _BLOCK_SIZE
def pad_text(text : str) -> bytearray:
    return pad_data(text.encode())

# Return a bytearray representing the given text
# to be used in AES-ECB encoding and decoding
def text_data(text : str) -> bytearray:
    data = bytearray(1)
    data[0] = len(text)
    data = data + text.encode()
    return pad_data(data)

# pretty print a bytearray
def str_data(ba : bytearray):
    if len(ba) == 0:
        return '[]'
    sba = '['
    for i in range(len(ba)):
        sba = sba + f'{ba[i]}, '
    sba = sba[:-2] + ']'
    return sba

# Return a bytearray representing the given bytearray
# to be used in AES-ECB encoding and decoding
# Need length for correct decoding
def byte_data(ba : bytearray) -> bytearray:
    data = bytearray(len(ba) + 1)
    data[0] = len(ba)
    for i in range(len(ba)):
        data[i+1] = ba[i]
    return pad_data(data)

# calculate simple checksum from bytearray
def checksum(data : bytearray) -> int:
    if data is None:
        return 0
    xor : int = 0
    for val in data:
        xor = xor ^ val
    return xor

# calculate twos complement of a 16 bit unsigned integer
def uint16_to_dec(uint16 : int) -> int:
    uint16 &= 0xFFFF
    if uint16 >= 0x8000:
        return -32768 + (uint16 - 0x8000)
    else:
        return uint16

# calculate twos complement of an 8 bit unsigned integer
def uint8_to_dec(uint8 : int) -> int:
    uint8 &= 0xFF
    if uint8 > 0x80:
        return -128 + (uint8 - 0x80)
    else:
        return uint8
    
# return a random integer in the indicated range
# limit values may be returned
def randint(imin : int, imax : int) -> int:
    funcs = dir(random)
    if 'randint' in funcs:
        return random.randint(imin, imax)
    else:
        try:
            from uos import urandom
            b16 = urandom(2)
            u16 = (b16[0] << 8) + b16[1]
            return int(imin + (imax - imin) * u16 / 65535)
        except Exception as e:
            raise Exception(f'Error {e} - need another randint implementation')

# TAB, LF, CR are 'printable'
_bch = {9, 10, 13}

# Decode single byte to 'safe' or 'printable' ASCII
def safe_decode(bch : bytes):
    ch = ''
    val : int = bch[0]
    if val in _bch:
        ch = chr(val)
    elif val > 31 and val < 127:
        ch = chr(val)
    else:
        ch = '?'
    return ch

# Determine the current python platform
# expected result ikeys {'name', 'version', 'platform'}
# name = 'cpython' | 'micropython'
# version = 'maj.min.rel'
# platform = 'linux' | 'rp2' | 'rp2w' | 'esp32' | 'esp32s3' | 'esp8266'
def get_platform() -> {}:
    skeys = dir(sys)
    impl = sys.implementation
    ikeys = dir(impl)
    
    results = {'name':'', 'version':'0.0.0', 'platform':'micropython', 'cpu_model':''}
    
    if 'name' in ikeys:
        results['name'] = impl.name
        
    if 'version' in ikeys:
        sver = impl.version
        version = f'{sver[0]}.{sver[1]}.{sver[2]}'
        results['version'] = version

    # linux | rp2 | rp2w | esp32s3
    # if linux, define cpu_model using /proc/cpuinfo
    if 'platform' in skeys:
        if _debug:
            print('platform in sys')
        pform = sys.platform
        if pform == 'rp2' and impl._machine.find(' W ') >= 0:
            pform += 'w'
        if pform == 'esp32' and '_machine' in ikeys:
            if impl._machine.find('ESP32S3') >= 0:
                pform = 'esp32s3'
            elif impl._machine.find('S2_MINI') >= 0:
                pform = 'esp32s2mini'
                results['cpu_model'] = 'S2FN4R2'
            elif impl._machine.find('ESP32S3') >= 0:
                pform = 'esp32s3'
        if pform == 'esp32' and board.find('esp32c') >= 0:
            results['cpu_model'] = 'ESP32-CAM'
        results['platform'] = pform
        if _debug:
            print(f'platform {pform}')
        if file_exists('/proc/cpuinfo'):
            if _debug:
                print('/proc/cpuinfo exists')
            fd = open('/proc/cpuinfo', 'r')
            line = fd.readline()
            while len(line) > 0:
                # linux on Intel
                if line.find('model name') == 0:
                    fields = line.split(':')
                    if len(fields) == 2:
                        """
                        for ch in fields[1]:
                            print(f'0x{ord(ch):02X} ', end='')
                        print()
                        """
                        results['cpu_model'] = fields[1][1:-1]
                        if _debug:
                            print('cpu_model {results["cpu_model"]}')
                        break
                # linux on rpi3/rpi4
                if line.find('Model') == 0:
                    fields = line.split(':')
                    if len(fields) == 2:
                        """
                        for ch in fields[1]:
                            print(f'0x{ord(ch):02X} ', end='')
                        print()
                        """
                        results['cpu_model'] = fields[1][1:-1]
                        if _debug:
                            print('cpu_model {results["cpu_model"]}')
                        break
                line = fd.readline()
    elif 'platform' in ikeys:
        if _debug:
            print('platform in sys.implementation')
        results['platform'] = sys.implementation['platform']
    elif '_machine' in ikeys:
        if _debug:
            print('_machine in sys.implementation')
        if 'Pico' in impl._machine:
            results['platform'] = 'pico'
        elif 'ESP8266' in impl._machine:
            results['platform'] = 'esp8266'
        elif 'ESP32S3' in impl._machine:
            results['platform'] = 'esp32s3'
            print('OK')
        elif 'ESP' in impl._machine:
            results['platform'] = 'esp32'
    else:
        if module_available('esp32'):
            results['platform'] = 'esp32'
        elif module_available('esp'):
            results['platform'] = 'esp8266'
    if _debug:
        print(f'platform is {results["platform"]}')
    return results

# Return True if the indicated file exists
def file_exists(filename : str) -> bool:
    try:
        fd = open(filename, 'r')
        fd.close()
    except OSError:
        return False
    return True

# Return the byte size of the indicated file, -1 if an OSError occurs
def file_size(filename : str) -> int:
    try:
        stats = os.stat(filename)
        return stats[6]
    except OSError:
        return -1

# Get the name of the current board, else _UNDEFINED
# Parse board.py file...
def get_board_name() -> str:
    board_name = _UNDEFINED
    board_file = 'board.py'
    
    if file_exists(board_file):
        with open(board_file, 'r') as fd:
            line = fd.readline()
            
            while line is not None and len(line) > 0:
                fields = line[:-1].split('=')
                if len(fields) == 2 and fields[0] == 'name':
                    board_name = fields[1][1:-1]
                    break
                line = fd.readline()
    elif _debug:
        print(f'Board config file {board_file} does not exist')
    if _debug:
        print(f'Board name is {board_name}')
    return board_name

# Get a unique board identifier byte string, else 6*b'0'
def get_unique_id() -> bytes:
    import machine
    attrs = dir(machine)
    if 'unique_id' in attrs:
        return machine.unique_id()
    else:
        return b'0x0' * 6

# Stringify the board ID
def strUniqueID() -> str:
    id = get_unique_id()
    sid = ''
    for num in id:
        sid = sid + f'{num:02x}.'
    return sid[:-1]

# Get the network MAC address, 6*b'0' is not defined
def get_mac_address(lan=None) -> bytes:
    if lan:
        return lan.wlan.config('mac')
    elif not module_available('lan'):
        return b'0x0' * 6
    from lan import LAN
    lan = LAN()
    if lan.connect():
        return lan.wlan.config('mac')
    else:
        return b'0x0' * 6

# Stringify the MAC address
def strMacAddress(lan=None, mac=None) -> str:
    if not mac:
        mac = get_mac_address(lan)
    smac = ''
    for num in mac:
        smac = smac + f'{num:02x}.'
    return smac[:-1]

# Return configuration information stored in the indicated file
def get_config(file) -> {}:
    if not file_exists(file):
        return {}
    try:
        with open(file, 'r') as fd:
            cfg = json.load(fd)
        return cfg
    except OSError:
        pass
    return {}

# Return the board configuration filename
def get_board_config_file() -> str:
    name = get_board_name()
    if name == _UNDEFINED:
        if _debug:
            print('Board name not set')
        return ''
    return f'{name}.cfg'

# Return the board configuration, {} if an error occurs
def get_board_config() -> {}:
    fname = get_board_config_file()
    if fname == '':
        if _debug:
            print('Board name not set')
        return {}
    return get_config(fname)

# Return the value of an optional configuration setting
# Return the default value if an error occurs
def get_setting(name : str, default, cfg : {}):
    result = default
    if name in cfg:
        result = cfg[name]
    return result

# Return True if the platform is an ESP32
def is_esp32() -> bool:
    return module_available('esp32')

# Return the CPU temperature on an ESP32 platform
def esp_cpu_temperature():
    import esp32
    if 'mcu_temperature' in dir(esp32):
        rawT = esp32.mcu_temperature()
    else:
        rawT = esp32.raw_temperature()
    if board.find('esp32s2m') >= 0:
        return rawT
    elif board.find('esp32c') < 0:
        return (rawT - 32) * 5 / 9
    else:
        return rawT - 100

# Return the CPU temperature on a Raspberry PI or ZERO platform
def rpi_cpu_temperature():
    temp = -99.0
    import os
    fname = 'temp_tmp.txt'
    result = os.system(f'vcgencmd measure_temp >{fname}')
    if result != 0:
        print(f'vcgencmd returned {result}')
        return temp
    if not file_exists(fname):
        print('os.system call did not work as expected')
        return temp
    with open(fname, 'r') as fd:
        stemp = fd.readline()
    os.remove(fname)
    eqpos = stemp.find("=")
    appos = stemp.find("'")
    if eqpos != -1 and appos != -1:
        temp = stemp[eqpos+1:appos]
        return float(temp)
    else:
        print(f'vcgencmd output format error \'{stemp}\'')

# Return the CPU temperature on a Raspberry PI PICO platform
ADC4 = None
def pico_cpu_temperature():
    global ADC4
    if ADC4 is None:
        from machine import ADC
        ADCPIN = 4
        ADC4 = ADC(ADCPIN)

    cnt = 5
    sum = 0
    while cnt > 0:
        val = ADC4.read_u16()
        sum += val
        cnt -= 1
    volt = sum / 5.0 * 3.3 / 65535
    return 27.0 - (volt - 0.706) / 0.001721

# Return the number of milliseconds since the EPOCH started or
# some other arbitrary point in time.
# Note: calculating with time_ns does not work on some platforms
def time_ms():
    if 'time_ms' in dir(time):
        return time.time_ms()
    elif platform == 'linux':
        return int((time.time_ns() + 500_000) / 1_000_000)
    else:
        st = f'{time.time_ns()}'
        return int(st[:-6])

# Return time in milliseconds since start of EPOCH 2000
# This value should be nearly the same on any synchronized platform.
# Note: this can be used to simultaneously monitor time sensitive events.
def debug_time_ms():
    return int(time_ms() - e2000_ms)

# Return platform independent timestamp as string (wrap at ~16min)
def debug_timestamp():
    stime = f'{debug_time_ms() % 1_000_000:06}'
    return f'{stime[:3]}.{stime[3:]}'

# Only works if time.time() returns UTC
# DST determination for germany
def is_dst():
    utc = time.time()
    return any(lwr <= utc < upr for (lwr, upr) in dst_ranges)

# Return the local time as a tuple
# TZ and DST compensation for germany
def localtime(tz=None, dst=None):
    if platform == 'linux':
        lt = time.localtime()
        return (lt[0], lt[1], lt[2], lt[3], lt[4], lt[5], lt[6], lt[7])
    else:
        tz = 1
        if tz is not None:
            tz = tz
        dst = 0
        if dst is not None:
            dst = dst
        elif is_dst():
            dst = 1
        local_offset = (tz + dst) * 3600
        return time.localtime(time.time()+local_offset)

# Convert date/time tuple to european string time representation
# if dow = True, tuple contains dow in [3]
# if short = True, return year field as 2 digits
def strDateTime(lt, dow=False, short=False):
    year = f'{lt[0]-2000:02}' if short else f'{lt[0]}'
    if dow:
        return f'{lt[2]:02d}.{lt[1]:02d}.{year} {lt[4]:02d}:{lt[5]:02d}:{lt[6]:02d}'
    else:
        return f'{lt[2]:02d}.{lt[1]:02d}.{year} {lt[3]:02d}:{lt[4]:02d}:{lt[5]:02d}'

# Convert localtime tuple to european string date representation
def strDate(short=False):
    tm = localtime()
    year = f'{tm[0]-2000:02}' if short else f'{tm[0]}'
    return(f'{tm[2]:02}.{tm[1]:02}.{year}')
    
# Convert localtime tuple to european string time representation
def strTime():
    tm = localtime()
    return(f'{tm[3]:02}:{tm[4]:02}:{tm[5]:02}')

# Return a string representation of cycles per second in Hz, KHz, Mhz, GHz
def niceCycles(cycles, space=True):
    assert(cycles >= 0)
    sep = ''
    if space:
        sep = ' '
    if cycles < 1000:
        return f'{cycles}{sep}Hz'
    khz = cycles / 1000
    if khz < 1000:
        return f'{khz:0.2f}{sep}KHz'
    mhz = khz / 1000
    if mhz < 1000:
        return f'{mhz:0.2f}{sep}MHz'
    ghz = mhz / 1000
    return f'{ghz:0.2f}{sep}GHz'

# Return a string representation of byte size in Kb, Mb, Gb
def niceSize(count, space=True):
    assert(count >= 0)
    sep = ''
    if space:
        sep = ' '
    if count < 1000:
        return f'{count}'
    kb = count / 1000
    if kb < 1000:
        return f'{kb:0.2f}{sep}Kb'
    mb = kb / 1000
    if mb < 1000:
        return f'{mb:0.2f}{sep}Mb'
    gb = mb / 1000
    return f'{gb:0.2f}{sep}Gb'

# Return a string representation of seconds as 'Dd Hh Mm Ss'
# If not space, return 'DdHhMmSs'
def niceSeconds(secs, space=True):
    sep = ''
    if space:
        sep = ' '
    sign = ''
    if secs < 0:
        secs = -secs
        sign = '-'
    isec = int(secs + 0.5)
    if isec < 60:
        return f'{sign}{isec}s'
    imin = int(isec / 60)
    isec = isec - imin * 60
    ssec = f'{sep}{isec}s'
    if isec == 0:
        ssec = ''
    if imin < 60:
        return f'{sign}{imin}m{ssec}'
    ihour = int(imin / 60)
    imin = imin - ihour * 60
    smin = f'{sep}{imin}m'
    if imin == 0:
        smin = ''
    if ihour < 24:
        return f'{sign}{ihour}h{smin}{ssec}'
    iday = int(ihour / 24)
    ihour = ihour - iday * 24
    shour = f'{sep}{ihour}h'
    if ihour == 0:
        shour = ''
    return f'{sign}{iday}d{shour}{smin}{ssec}'

# Return a 'nice' number (factor of 1, 2, 5, 10) larger
# larger or smaller in absolute value than the input value.
def niceNumber(num : float, round=False) -> float:
    from math import log10, pow, floor
    
    if num == 0:
        return 0

    neg = num < 0
    if neg:
        num = -num

    expt = floor(log10(num))
    frac = num / pow(10.0, float(expt))
    if round:
        if frac < 1.5:
            nice = 1.0
        elif frac < 3.0:
            nice = 2.0
        elif frac < 7.0:
            nice = 5.0
        else:
            nice = 10.0
    else:
        if frac <= 1.0:
            nice = 1.0
        elif frac <= 2.0:
            nice = 2.0
        elif frac <= 5.0:
            nice = 5.0
        else:
            nice = 10.0
    
    result = nice * pow(10.0, float(expt))
    return result if not neg else -result

# platform independent tick addition
def local_ticks_add(val1, val2):
    if platform == 'linux':
        return val1 + val2
    else:
        return time.ticks_add(val1, val2)

# platform independent tick subtraction
def local_ticks_diff(val1, val2):
    if platform == 'linux':
        return val1 - val2
    else:
        return time.ticks_diff(val1, val2)

# platform independent millisecond timer
def local_ticks_ms():
    if platform == 'linux':
        return int((time.time_ns()+500000)/1000000)
    else:
        return time.ticks_ms()

# platform independent callback handler
def print_exception(e):
    if module_available('traceback'):
        import traceback
        traceback.print_exception(e)
    else:
        sys.print_exception(e)

# Initialize platform independent cryptography support
if module_available('cryptolib'):
    import cryptolib
    _MODE_ECB = 1
    get_cipher = cryptolib.aes
elif _debug:
    print('cryptolib not available')
    
if module_available('Cryptodome.Cipher'):
    from Cryptodome.Cipher import AES
    _MODE_ECB = AES.MODE_ECB
    get_cipher = AES.new
elif _debug:
    print('Cryptodome not available')

if _debug and get_cipher is None:
    print('Cryptography support is not available')

# Initialize global board name
board = get_board_name()

# Initialize platform independent CPU temperature function
if board.find('esp32') == 0:
    get_cpu_temperature = esp_cpu_temperature
elif board.find('rpi') == 0:
    get_cpu_temperature = rpi_cpu_temperature
elif board.find('pico') == 0:
    get_cpu_temperature =  pico_cpu_temperature

if _debug and get_cpu_temperature is None:
    print('CPU temperature support is not available')

# Get global platform dictionary
_info = get_platform()
platform = _info['platform']

# Initialize global EPOCH 2000 value
if platform == 'linux':
    # mktime on linux uses localtime, not UTC time
    e2000 = int(time.mktime((2000, 1, 1, 0, 0, 0, 5, 1, 0))+0.5) + 3600
else:
    e2000 = int(time.mktime((2000, 1, 1, 0, 0, 0, 5, 1)))
e2000_ms = e2000 * 1000
