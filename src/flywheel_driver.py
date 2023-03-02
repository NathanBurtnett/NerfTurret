import pyb


class Flywheel:
    def __init__(self, pwm_pin, freq=200):
        # Configure PWM output pin
        self.pwm = pyb.PWM(pwm_pin, freq=freq)
        self.max_pulse_width = 2000
        self.min_pulse_width = 1000

    def arm(self, min_percent=5.0):
        # Set throttle to minimum for a few seconds to arm the ESC
        self.set_percent(min_percent)

    def set_percent(self, percent):
        if percent > 100:
            percent = 100
        elif percent < 0:
            percent = 0
        pulse_width = percent * self.max_pulse_width
        self.pwm_pin.pulse_width(pulse_width / 100)

    def release(self):
        # Set to minimum motor speed
        self.pwm.pin.pulse_width(self.min_pulse_width)
