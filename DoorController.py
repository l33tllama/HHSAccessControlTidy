import pigpio
import wiegand
import time, sched
from threading import Timer

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
        self.nopigpio = nopigpio
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
                                       self._tag_scanned, self.unknown_pin_d)
        print("GPIO setup complete?")

    def _pin_on(self, pin):
        print("Pin " + str(pin) + " on")
        if self.nopigpio is False:
            self.pi.set_mode(pin, pigpio.OUTPUT)
            self.pi.write(pin, 1)

    def _pin_off(self, pin):
        print("Pin " + str(pin) + " off")
        if self.nopigpio is False:
            self.pi.set_mode(pin, pigpio.OUTPUT)
            self.pi.write(pin, 0)

    def is_alarm_armed(self):
        status = self.pi.read(self.alarm_armed_status_pin) == 0
        return status

    def toggle_alarm_pin(self):
        self._pin_on(self.alarm_toggle_pin)
        Timer(3, self._pin_off, args=[self.alarm_toggle_pin])
        pass

    def _alarm_arming(self):
        self.arming_alarm = False

    def _tag_scanned(self, bits, rfid):
        if callable(self.tag_scanned_cb):
            self.tag_scanned_cb(bits, rfid)
        else:
            print("ERROR: tag scanned callback not callable.")

    # When the alarm arm button is pressed
    def arm_alarm(self):
        if self.arming_alarm:
            return
        self.arming_alarm = True

        Timer(10, self._alarm_arming)

        # if alarm is not already armed
        if not self.is_alamr_armed():
            self.toggle_alarm_pin()

        self._pin_off(self.buzzer_pin)
        Timer(8, self._pin_on, args=[self.buzzer_pin])

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
        print("Unlocking door..")
        self._pin_on(self.door_strike_pin)
        Timer(6.5, self._pin_off, args=[self.door_strike_pin]).start()
        Timer(0.1, self._pin_off, args=[self.buzzer_pin]).start()
        Timer(1.0, self._pin_on, args=[self.buzzer_pin]).start()

    def set_tag_scanned_callback(self, callback):
        if callable(callback):
            self.tag_scanned_cb = callback
        else:
            print("ERROR: tag scanned callback not callable" )

    def set_alarm_sounding_callback(self, callback):
        if(callable(callback)):
            self.alarm_sounding_cb = callback
        else:
            print("ERROR: alarm sounding callback not callable")