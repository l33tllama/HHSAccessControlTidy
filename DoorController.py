
import pigpio
import wiegand
import time, sched

class DoorController():

    def __init__(self, nopigpio=False):
        self.arm_alarm_button_pin = 3
        self.alarm_toggle_pin = 10
        self.alarm_armed_status_pin = 6
        self.alarm_sounding_status_pin = 7
        self.door_strike_pin = 22
        self.buzzer_pin = 24 # buzzer?
        self.unknown_pin_b = 27
        self.unknown_pin_c = 17
        self.unknown_pin_d = 25
        self.alarm_sounding = False
        self.arming_alarm = False
        self.tag_scanned_cb = None
        self.alarm_sounding_cb = None
        self.wiegand = None
        self.sched = sched.scheduler(time.time, time.sleep)
        if nopigpio is False:
            self._setup_gpio()

    def on_end(self):
        self.wiegand.cancel()
        self.pi.stop()

    def _setup_gpio(self):
        self.pi = pigpio.pi()
        self.pi.write(self.buzzer_pin, 1)
        a = self.pi.callback(self.arm_alarm_button_pin, pigpio.FALLING_EDGE, self.arm_alarm)
        b = self.pi.callback(self.alarm_sounding_status_pin, pigpio.FALLING_EDGE, self.alarm_sounding)
        self.wiegand = wiegand.decoder(self.pi,
                                       self.unknown_pin_b, self.unknown_pin_c,
                                       self.tag_scanned_cb, self.unknown_pin_d)

    def _pin_on(self, pin):
        self.pi.set_mode(pin, pigpio.OUTPUT)
        self.pi.write(pin, 1)

    def _pin_off(self, pin):
        self.pi.set_mode(pin, pigpio.OUTPUT)
        self.pi.write(pin, 0)

    def is_alarm_armed(self):
        status = self.pi.read(self.alarm_armed_status_pin) == 0
        return status

    def toggle_alarm_pin(self):
        self._pin_on(self.alarm_toggle_pin)
        self.sched.enter(3, 1, self._pin_off, (self.alarm_toggle_pin))
        pass

    def _alarm_arming(self):
        self.arming_alarm = False

    # When the alarm arm button is pressed
    def arm_alarm(self):
        if self.arming_alarm:
            return
        self.arming_alarm = True

        self.sched.enter(10, 1, self._alarm_arming, ())

        self.sched.enter()
        # if alarm is not already armed
        if not self.is_alamr_armed():
            self.toggle_alarm_pin()

        self._pin_off(self.buzzer_pin)
        self.sched.enter(8, 1, self._pin_on, (self.buzzer_pin))

        # TODO: log alarm armed

    # When the alarm is sounding (someone in before alarm disabled..)
    def alarm_sounding(self, gpio, level, tick):
        if not self.alarm_sounding:
            # debounce
            time.sleep(2)
            if(self.pi.read(self.alarm_sounding_status_pin) == 1):
                print "debounced"
                return
            if callable(self.alarm_sounding_cb):
                self.alarm_sounding_cb()
            self.alarm_sounding = True

    def unlock_door(self):
        self._pin_on(self.door_strike_pin)
        self.sched.enter(6.5, 1, self._pin_off, (self.door_strike_pin))
        self.sched.enter(0.1, 1, self._pin_off, (self.buzzer_pin))
        self.sched.enter(1.0, 1, self._pin_on, (self.buzzer_pin))

    def set_tag_scanned_callback(self, callback):
        if callable(callback):
            self.tag_scanned_cb = callback

    def set_alarm_sounding_callback(self, callback):
        if(callable(callback)):
            self.alarm_sounding_cb = callback