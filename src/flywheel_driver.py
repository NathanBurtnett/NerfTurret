import pyb


class Flywheel:
    def __init__(self, pwm_pin, timer, channel, freq=200):
        self.tim = pyb.Timer(timer, freq=freq)
        self.ch = self.tim.channel(channel, pyb.Timer.PWM, pin=pwm_pin)
        self.min_pulse_width = 700
        self.max_pulse_width = 2500

    def set_percent(self, percent):
        pulse_width = int(percent * 0.1 * (self.max_pulse_width - self.min_pulse_width) + self.min_pulse_width)
        self.ch.pulse_width(pulse_width * 100)

    def set_speed(self, speed):
        self.ch.pulse_width(speed*100*4//5)
