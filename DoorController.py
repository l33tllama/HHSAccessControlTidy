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
        self.alarm_armed_cb = None
        self.wiegand = None

        self.sched = sched.scheduler(time.time, time.sleep)
        self.nopigpio = nopigpio

        if nopigpio is False:
            print ("PiGPIO enabled.")
        else:
            print ("PiGPIO disabled.")

        if nopigpio is False:
            self._setup_gpio()

    # When program ends
    def on_end(self):
        self.wiegand.cancel()
        self.pi.stop()

    # Setup when PiGPIO is enabled (on device)
    def _setup_gpio(self):
        self.pi = pigpio.pi()
        self.pi.write(self.buzzer_pin, 1)
        a = self.pi.callback(self.arm_alarm_button_pin, pigpio.FALLING_EDGE, self._arm_alarm)
        b = self.pi.callback(self.alarm_sounding_status_pin, pigpio.FALLING_EDGE, self._alarm_sounding)
        self.wiegand = wiegand.decoder(self.pi,
                                       self.unknown_pin_b, self.unknown_pin_c,
                                       self._tag_scanned, self.unknown_pin_d)
        print("GPIO setup complete.")

    # Pin ON
    def _pin_on(self, pin):
        if self.nopigpio is False:
            self.pi.set_mode(pin, pigpio.OUTPUT)
            self.pi.write(pin, 1)

    # Pin OFF
    def _pin_off(self, pin):
        if self.nopigpio is False:
            self.pi.set_mode(pin, pigpio.OUTPUT)
            self.pi.write(pin, 0)

    # Get status of alarm armed status by reading pin
    def is_alarm_armed(self):
        status = self.pi.read(self.alarm_armed_status_pin) == 0
        return status

    # Toggle the arm alarm pin
    def toggle_alarm_pin(self):
        if self.is_alarm_armed():
            self._pin_on(self.alarm_toggle_pin)
            Timer(3, self._pin_off, args=[self.alarm_toggle_pin])
        pass

    # timeout when arming alarm has finished (gives you chance to leave the building..)
    def _alarm_armed(self):
        self.arming_alarm = False
        if callable(self.alarm_armed_cb):
            self.alarm_armed_cb()

    # Internal tag scanned callback (calls main callback also)
    def _tag_scanned(self, bits, rfid):
        if callable(self.tag_scanned_cb):
            self.tag_scanned_cb(bits, rfid)
        else:
            print("ERROR: tag scanned callback not callable.")

    # When the alarm is sounding (someone in before alarm disabled..)
    def _alarm_sounding(self, gpio, level, tick):
        if not self.alarm_sounding:
            # debounce
            time.sleep(2)
            if self.pi.read(self.alarm_sounding_status_pin) == 1:
                print "debounced"
                return
            # alert people!
            if callable(self.alarm_sounding_cb):
                self.alarm_sounding_cb()
            self.alarm_sounding = True

    # Arm alarm pin callback
    def _arm_alarm(self, gpio, level, tick):

        if self.arming_alarm:
            return

        self.arming_alarm = True

        Timer(10, self._alarm_armed)

        # if alarm is not already armed
        if not self.is_alamr_armed():
            self.toggle_alarm_pin()

        self._pin_off(self.buzzer_pin)
        Timer(8, self._pin_on, args=[self.buzzer_pin])

    # Called from main - open the door!
    def unlock_door(self):
        if self.alarm_sounding:
            self.alarm_sounding = False

        if self.is_alarm_armed():
            self.toggle_alarm_pin()

        self._pin_on(self.door_strike_pin)
        Timer(6.5, self._pin_off, args=[self.door_strike_pin]).start()
        Timer(0.1, self._pin_off, args=[self.buzzer_pin]).start()
        Timer(1.0, self._pin_on, args=[self.buzzer_pin]).start()

    # set the tag scanned callback (make sure it's callable)
    def set_tag_scanned_callback(self, callback):

        if callable(callback):
            self.tag_scanned_cb = callback
        else:
            print("ERROR: tag scanned callback not callable" )

    # set the alarm sounding callback (make sure it's callable)
    def set_alarm_sounding_callback(self, callback):
        if(callable(callback)):
            self.alarm_sounding_cb = callback
        else:
            print("ERROR: alarm sounding callback not callable")

    # set the alarm armed callback (make sure it's callable)
    def set_alarm_armed_callback(self, callback):
        if (callable(callback)):
            self.alarm_armed_cb = callback
        else:
            print("ERROR: alarm sounding callback not callable")