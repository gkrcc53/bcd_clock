# platform independent library to perform common network functions
#
# Configuration (* --> required)
#   debug           - False if not defined
#   ntp_host        - pool.ntp.org if not defined
#   ssid            * Local Netword ID
#   ssid_password   * Local Network password
#   country         - DE if not defined
#   hostname        - set to board name if not defined, see Notes
#
# Notes
#   If the hostname and board name are both not defined
#   the hostname is set to the platform name string

import sys
import network
import time
import socket
import struct
import uctypes
import urandom
import uselect
import ustruct
import genlib as gl

class LAN:
    def __init__(self):
        # some network implementation do not support STAT_CONNECT_FAIL
        self.hasFail = 'STAT_CONNECT_FAIL' in dir(network)
        cfg = gl.get_board_config()
        lcfg = gl.get_config('lan.cfg')
        # LAN configuration can override default board configuration
        self.cfg = cfg | lcfg
        self.keys = self.cfg.keys()
        self.connected = False
        self.wlan = None
        self.ntp_host = 'pool.ntp.org'
        if 'ntp_host' in self.keys:
            self.ntp_host = cfg['ntp_host']
        self._debug = 'debug' in self.keys and self.cfg['debug']
        if self._debug:
            for key in sorted(self.keys):
                print(f'{key:<20}{self.cfg[key]}')
            print()

    @property
    def debug(self):
        return self._debug

    @debug.setter
    def debug(self, val):
        self._debug = val

    def config(self):
        return self.cfg

    def wlan(self):
        return self.wlan
    
    def get_ip(self):
        if not self.wlan:
            return '0.0.0.0'
        else:
            return self.wlan.ifconfig()[0]

    def _strNetStatus(self, status):
        if status == network.STAT_CONNECTING:
            return 'CONNECTING'
        elif self.hasFail and status == network.STAT_CONNECT_FAIL:
            return 'CONNECT_FAIL'
        elif status == network.STAT_GOT_IP:
            return 'GOT_IP'
        elif status == network.STAT_IDLE:
            return 'IDLE'
        elif status == network.STAT_NO_AP_FOUND:
            return 'NO_AP_FOUND'
        elif status == network.STAT_WRONG_PASSWORD:
            return 'WRONG_PASSWORD'
        else:
            return f'{status}'

    def is_connected(self):
        if self.wlan:
            self.connected = self.wlan.isconnected()
        return self.connected

    def connect(self, tries=5):
        if self.is_connected():
            return True

        # Get ssid from configuration file
        if 'ssid' not in self.keys:
            print('LAN ssid not configured')
            return False
        ssid = self.cfg['ssid']

        # Get ssid_password from configuration file
        if 'ssid_password' not in self.keys:
            print('LAN password not configured')
            return False
        pwrd = self.cfg['ssid_password']

        esp32cam = gl.get_platform()['cpu_model'] == 'ESP32-CAM'
        if not esp32cam:
            # Set country
            country = 'DE'
            if 'country' in self.cfg:
                country = self.cfg['country']
            network.country(country)
            if self._debug:
                print(f'country set to {network.country()}')

            # Set hostname
            hostname = gl.get_board_name()
            if 'hostname' in self.cfg:
                hostname = self.cfg['hostname']
            if hostname == gl._UNDEFINED:
                hostname = gl.platform
            network.hostname(hostname)
            if self._debug:
                print(f'hostname set to {network.hostname()}')
        
        # Try to connect
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        time.sleep(1)
        if self._debug:
            print(f'Trying to connect to {ssid}')
        try:
            cnt1 = tries
            while cnt1 > 0:
                self.wlan.connect(ssid, pwrd)
                cnt2 = 5
                while cnt2 > 0:
                    status = self.wlan.status()
                    if status == network.STAT_GOT_IP:
                        self.connected = True
                        if self._debug:
                            print(f'Connected to LAN - ip is {self.wlan.ifconfig()[0]}')
                        return True
                    time.sleep(1)
                    if self._debug:
                        print(f'wlan status is {self._strNetStatus(status)}')
                    cnt2 -= 1
                if self.connected:
                    break
                self.wlan.disconnect()
                time.sleep(5)
                cnt1 -= 1
            return False
        except Exception as e:
            print(f'Error {e}')
            return False

    def disconnect(self):
        if not self.is_connected():
            return
        if self.wlan:
            self.wlan.disconnect()
            self.wlan.active(False)
        self.connected = False
        if self._debug:
            print('Disconnected from LAN')

    # return UTC time from NTP server without TZ/DST modification
    def ntp_socket(self, host, timeout=10):
        NTP_QUERY = bytearray(48)
        NTP_QUERY[0] = 0x1B

        if not host or len(host) == 0:
            host = 'pool.ntp.org'
        
        is_open = False
        msg = None
        msgOK = False
        try:
            addr = socket.getaddrinfo(host, 123)[0][-1]
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            is_open = True
            s.settimeout(timeout)
            s.sendto(NTP_QUERY, addr)
            msg = s.recv(48)
            msgOK = True
        except Exception as e:
            if self._debug:
                print(f'Exception \'{e}\' ignored in ntp_time', 3)
        finally:
            if is_open:
                s.close()
            
        if msgOK:
            val = struct.unpack("!I", msg[40:44])[0]
            
            EPOCH_YEAR = time.gmtime(0)[0]
            if EPOCH_YEAR == 2000:
                # (date(2000, 1, 1) - date(1900, 1, 1)).days * 24*60*60
                NTP_DELTA = 3155673600
            elif EPOCH_YEAR == 1970:
                # (date(1970, 1, 1) - date(1900, 1, 1)).days * 24*60*60
                NTP_DELTA = 2208988800
            else:
                raise Exception("Unsupported epoch: {}".format(EPOCH_YEAR))

            return val - NTP_DELTA
        else:
            return 0

    # return UTC time from ntptime module
    def ntp_time(self, host=None, timeout=10):
        if not gl.module_available('ntptime'):
            return 0
        
        if not self.is_connected() and not self.connect():
            return False
    
        import ntptime
        ntptime.host = self.ntp_host if host is None else host
        ntptime.timeout = timeout
        cnt = 5
        while cnt > 0:
            try:
                utc = ntptime.time()
                return utc
            except Exception:
                pass
            cnt -= 1
        return 0

    def update_rtc(self, host=None, timeout=10):
        from machine import RTC
        ltime = self.ntp_time(host, timeout)
        if ltime == 0:
            ltime = self.ntp_socket(host, timeout)
        if ltime == 0:
            return False
        lt = time.gmtime(ltime)
        RTC().datetime((lt[0], lt[1], lt[2], lt[6], lt[3], lt[4], lt[5], 0))
        lt = time.gmtime()
        if self._debug:
            print(f'UTC time is {lt[3]:02}:{lt[4]:02}:{lt[5]:02} on {lt[2]:02}.{lt[1]:02}.{lt[0]}')
        return True

    def url_encode(self, string):
       encoded_string = ""
       for character in string:
           if character.isalpha() or character.isdigit():
               encoded_string += character
           else:
               encoded_string += f"%{ord(character):x}"
       return encoded_string
        
    def url_decode(self, url):
        counter = 0
        # A check to break out of the loop after 100 iterations
        while '%' in url and counter < 100:
            index = url.index('%')
            hex_code = url[index+1:index+3]
            char = chr(int(hex_code, 16))
            url = url[:index] + char + url[index+3:]
            counter += 1  
        return url

    def _checksum(self, data):
        if len(data) & 0x1: # Odd number of bytes
            data += b'\0'
        cs = 0
        for pos in range(0, len(data), 2):
            b1 = data[pos]
            b2 = data[pos + 1]
            cs += (b1 << 8) + b2
        while cs >= 0x10000:
            cs = (cs & 0xffff) + (cs >> 16)
        cs = ~cs & 0xffff
        return cs

    def ping(self, host, count=5, timeout=5000, interval=200, quiet=False, size=64):
        try:
            # prepare packet
            assert size >= 16, "pkt size too small"
            pkt = b'Q'*size
            pkt_desc = {
                "type": uctypes.UINT8 | 0,
                "code": uctypes.UINT8 | 1,
                "checksum": uctypes.UINT16 | 2,
                "id": uctypes.UINT16 | 4,
                "seq": uctypes.INT16 | 6,
                "timestamp": uctypes.UINT64 | 8,
            } # packet header descriptor
            h = uctypes.struct(uctypes.addressof(pkt), pkt_desc, uctypes.BIG_ENDIAN)
            h.type = 8 # ICMP_ECHO_REQUEST
            h.code = 0
            h.checksum = 0
            h.id = urandom.getrandbits(16)
            h.seq = 1

            # init socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, 1)
            sock.setblocking(0)
            sock.settimeout(timeout/1000)
            addr = socket.getaddrinfo(host, 1)[0][-1][0] # ip address
            sock.connect((addr, 1))
            if not quiet:
                print("PING %s (%s): %u data bytes" % (host, addr, len(pkt)))
            
            seqs = list(range(1, count+1)) # [1,2,...,count]
            c = 1
            t = 0
            n_trans = 0
            n_recv = 0
            finish = False
            while t < timeout:
                if t==interval and c<=count:
                    # send packet
                    h.checksum = 0
                    h.seq = c
                    h.timestamp = time.ticks_us()
                    h.checksum = self._checksum(pkt)
                    if sock.send(pkt) == size:
                        n_trans += 1
                        t = 0 # reset timeout
                    else:
                        seqs.remove(c)
                    c += 1

                # recv packet
                while 1:
                    socks, _, _ = uselect.select([sock], [], [], 0)
                    if socks:
                        resp = socks[0].recv(4096)
                        resp_mv = memoryview(resp)
                        h2 = uctypes.struct(uctypes.addressof(resp_mv[20:]), pkt_desc, uctypes.BIG_ENDIAN)
                        # TODO: validate checksum (optional)
                        seq = h2.seq
                        if h2.type==0 and h2.id==h.id and (seq in seqs): # 0: ICMP_ECHO_REPLY
                            t_elasped = (time.ticks_us()-h2.timestamp) / 1000
                            ttl = ustruct.unpack('!B', resp_mv[8:9])[0] # time-to-live
                            n_recv += 1
                            if not quiet:
                                print("%u bytes from %s: icmp_seq=%u, ttl=%u, time=%0.2f ms" % (len(resp), addr, seq, ttl, t_elasped))
                            seqs.remove(seq)
                            if len(seqs) == 0:
                                finish = True
                                break
                    else:
                        break

                if finish:
                    break

                time.sleep_ms(1)
                t += 1

            # close
            sock.close()
            if not quiet:
                print("%u packets transmitted, %u packets received" % (n_trans, n_recv))
            return (n_trans, n_recv)
        except Exception as e:
            sys.print_exception(f'Exception {e} while pinging {host} ignored')
            return (0, 0)
