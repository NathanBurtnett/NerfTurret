import pyb

import settings
import utime

class Flywheel:
    def __init__(self, pwm_pin, timer, channel, freq=50):
        """!
        Brief: The initial setup for the flywheel. Sets up the pin, timer, channel, and frequency
        for the flywheel motor along with any initial set points and time readings.
        :param pwm_pin: the pin to be used for pwm output
        :param timer: the timer to be used for the motor
        : param channel: the channel to be used for the motor
        :"""
        self.tim = pyb.Timer(timer, freq=freq)
        self.ch = self.tim.channel(channel, pyb.Timer.PWM, pin=pwm_pin)
        self.min_pulse_width = 3000
        self.max_pulse_width = 5000
        self.set_point = self.min_pulse_width
        self.actual = self.min_pulse_width
        self.t_prev = None

    def set_percent(self, percent):
        """!
        Brief: Takes the input to the function as a percentage and converts the percentage into the correct pulse width
        :param percent: the input percentage ranged from 0-100
        :return: the motor set point"""
        self.set_point = self.min_pulse_width + (percent / 100) * (self.max_pulse_width - self.min_pulse_width)

    def set_speed(self, speed):
        """!
        Brief: Takes the input speed and sets the set point in terms of ms for PWM control of the motor
        :param speed: the wanted speed of the motor
        :return: the set point of the motor"""
        self.set_point = speed * 1000

    def loop(self):
        """!
        Brief: Limits the ramp up of the motor while not limiting the ramp down
        :return: limited motor pulse width for ramp up"""
        t = utime.ticks_ms()
        self.t_prev = self.t_prev or t
        delta_t = (t - self.t_prev) / 1000

        # Limits ramp-ups, doesn't limit ramp-downs
        self.actual += min(self.set_point - self.actual, settings.max_ramp / delta_t) if delta_t > 0 else self.min_pulse_width
        self.ch.pulse_width(int(self.actual))
        # print("FWD", self.actual)
        self.t_prev = t

