import pyb

class Servo:
    def __init__(self, pin):
        self.tim = pyb.Timer(2, freq=200)
        self.ch = self.tim.channel(3, pyb.Timer.PWM, pin=pin)
        self.min_pulse_width = 500
        self.max_pulse_width = 2500
        self.is_set = False

    def set_angle(self, angle):
        pulse_width = int((angle) / 180.0 * (self.max_pulse_width - self.min_pulse_width) + self.min_pulse_width)
        self.ch.pulse_width(pulse_width*100)

    def set(self):
        self.set_angle(120)
        self.is_set = True

    def back(self):
        self.set_angle(75)
        self.is_set = False
