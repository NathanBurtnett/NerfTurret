import pyb


class Flywheel:
    def __init__(self, pwm_pin, freq=200):
        # Configure PWM output pin
        self.tim = pyb.Timer(3, freq=freq)
        self.ch = self.tim.channel(1, pyb.Timer.PWM, pin=pin)
        self.max_pulse_width = 2000
        self.min_pulse_width = 1000
        self.set_percent(0)

    def set_percent(self, percent):
        if percent > 100:
            percent = 100
        elif percent < 0:
            percent = 0
        pulse_width = percent * self.max_pulse_width
        self.pwm_pin.pulse_width(pulse_width / 100)