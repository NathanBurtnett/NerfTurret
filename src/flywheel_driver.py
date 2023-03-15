import pyb

import settings
import utime

class Flywheel:
    def __init__(self, pwm_pin, timer, channel, freq=50):
        self.tim = pyb.Timer(timer, freq=freq)
        self.ch = self.tim.channel(channel, pyb.Timer.PWM, pin=pwm_pin)
        self.min_pulse_width = 3000
        self.max_pulse_width = 5000
        self.set_point = self.min_pulse_width
        self.actual = self.min_pulse_width
        self.t_prev = None

    def set_percent(self, percent):
        self.set_point = self.min_pulse_width + (percent / 100) * (self.max_pulse_width - self.min_pulse_width)

    def set_speed(self, speed):
        self.set_point = speed * 1000

    def loop(self):
        t = utime.ticks_ms()
        self.t_prev = self.t_prev or t
        delta_t = (t - self.t_prev) / 1000

        # Limits ramp-ups, doesn't limit ramp-downs
        self.actual += min(self.set_point - self.actual, settings.max_ramp / delta_t) if delta_t > 0 else self.min_pulse_width
        self.ch.pulse_width(int(self.actual))
        # print("FWD", self.actual)
        self.t_prev = t

