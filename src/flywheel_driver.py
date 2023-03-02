import pyb

class Flywheel:
    def __init__(self, pwm_pin, freq=1000):
        # Configure PWM output pin
        self.pwm = pyb.PWM(pwm_pin, freq=freq)
        self.pwm_percent = 0.0

    def arm(self, min_percent=5.0):
        # Set throttle to minimum for a few seconds to arm the ESC
        self.set_percent(min_percent)

    def set_percent(self, percent):
        # Make sure throttle is within range
        percent = max(0.0, min(100.0, percent))
        # Convert percent from float in [0.0, 100.0] to PWM duty cycle in [0, 1023]
        duty_cycle = int(percent * 10.23)
        self.pwm_percent = percent
        self.pwm.duty(duty_cycle)

    def release(self):
        # Release PWM output pin
        self.pwm.deinit()
