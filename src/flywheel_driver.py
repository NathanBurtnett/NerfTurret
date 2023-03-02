import pyb


class Flywheel:
    def __init__(self, pwm_pin, freq=200):
        # Configure PWM output pin
        self.tim = pyb.Timer(2, freq=freq)
        self.ch = self.tim.channel(4, pyb.Timer.PWM, pin=pwm_pin)
        self.min_pulse_width = 1000
        self.max_pulse_width = 2000
        self.set_angle(0)

    def set_percent(self, percent):
        if percent > 100:
            percent = 100
        elif percent < 0:
            percent = 0
        pulse_width = percent * self.max_pulse_width
        self.ch.pulse_width(pulse_width)