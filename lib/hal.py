# Hardware abstraction layer
import genlib as gl


class HAL():
    def __init__(self):
        self._iolib = ''
        cfg = gl.get_board_config()
        cfg |= gl.get_config('hw.cfg')
        self._cfg = cfg
        self._debug = 'debug' in cfg and cfg['debug']
        if gl.module_available('gpiozero'):
            self._iolib = 'gpiozero'
        elif gl.module_available('machine'):
            import machine
            if 'Pin' not in dir(machine):
                raise Exception('machine.Pin not available')
            self._iolib = 'machine'
        else:
            raise Exception('IOLIB not available on this platform')

    @property
    def iolib(self):
        return self._iolib

    # return an LED class that support .on() and .off()
    def get_led(self, pin_id, *args, **kw):
        led = None
        if self._iolib == 'machine':
            from machine import Pin
            led = Pin(pin_id, Pin.OUT, *args, **kw)
        elif self.iolib == 'gpiozero':
            from gpiozero import LED
            led = LED(pin_id, *args, **kw)
        return led

    # disable an active button ISR
    def disable_button_isr(self, button):
        if self._iolib == 'machine':
            button.irq(handler=None)
#        else:
#            button.when_pressed = None
#            button.when_released = None

    # return a button class that supports .value()
    # and control an optional ISR
    def get_button(self, pin_id, pin_pull='up', pin_isr=None, trigger='fall'):
        button_pulls = ['up', 'down']
        button_triggers = ['rise', 'fall', 'both']

        btn = None
        if pin_pull not in button_pulls:
            raise Exception('Invalid button pull')
        if pin_isr is not None and trigger not in button_triggers:
            raise Exception('Invalid button trigger')
        if self._iolib == 'machine':
            from machine import Pin
            # Return simple button, no ISR
            pull = Pin.PULL_DOWN if pin_pull == 'down' else Pin.PULL_UP
            btn = Pin(pin_id, Pin.IN, pull)
            if pin_isr is None:
                return btn
            # Return button with active ISR
            if trigger == 'rise':
                btn.irq(handler=pin_isr,
                        trigger=Pin.IRQ_RISING)
            elif trigger == 'fall':
                btn.irq(handler=pin_isr,
                        trigger=Pin.IRQ_FALLING)
            else:
                btn.irq(handler=pin_isr,
                        trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING)
        elif self.iolib == 'gpiozero':
            from gpiozero import Button
            pull = False if pin_pull == 'down' else True
            btn = Button(pin_id, pull_up=pull, bounce_time=0.1)
            if trigger == 'rise':
                btn.when_released = pin_isr
            elif trigger == 'fall':
                btn.when_pressed = pin_isr
            else:
                btn.when_released = pin_isr
                btn.when_pressed = pin_isr
        return btn

    def get_lan(self):
        lan = None
        if gl.module_available('network'):
            if gl.file_exists('lan.cfg'):
                from lan import LAN
                lan = LAN()
                # lan.debug = True
                print('Trying to connect to LAN...')
                if lan is None or not lan.connect():
                    raise Exception('LAN connection failed')
                print(f'Connected to {lan.config()["ssid"]}')
                hcfg = gl.get_config('hw.cfg')
                if 'wlan_txpower' in hcfg:
                    txp = hcfg["wlan_txpower"]
                    lan.wlan.config(txpower=txp)
                txp = lan.wlan.config('txpower')
                if self._debug:
                    print(f'WLAN transmit power is {txp}')
                if not lan.update_rtc():
                    raise Exception('RTC update failed')
        return lan

    def get_time_direct(self):
        if self.iolib == 'machine':
            from machine import RTC
            return RTC().datetime()
        else:
            import time
            utc = time.localtime()
            return (utc.tm_year, utc.tm_mon, utc.tm_mday,
                    utc.tm_wday,
                    utc.tm.hour, utc.tm_min, utc.tm_sec,
                    0)
