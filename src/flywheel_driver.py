import pyb


class Flywheel:
    def __init__(self, pwm_pin, timer, channel, freq=50):
        self.tim = pyb.Timer(timer, freq=freq)
        self.ch = self.tim.channel(channel, pyb.Timer.PWM, pin=pwm_pin)
        self.min_pulse_width = 1000
        self.max_pulse_width = 2000

    def set_percent(self, percent):
        pulse_width = int(3000 + (percent/100)*2000)
        print(pulse_width)
        self.ch.pulse_width(pulse_width)

    def set_speed(self, speed):
        self.ch.pulse_width(speed*1000)
