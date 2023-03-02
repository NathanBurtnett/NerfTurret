import pyb

class Servo:
    def __init__(self, pin):
        freq = 200
        self.tim = pyb.Timer(3, freq=freq)
        self.ch = self.tim.channel(1, pyb.Timer.PWM, pin=pin)
        self.min_pulse_width = 500
        self.max_pulse_width = 2500
        self.set_angle(0)


    def set_angle(self, angle):
        pulse_width = int((angle + 90) / 180.0 * (self.max_pulse_width - self.min_pulse_width) + self.min_pulse_width)
        self.ch.pulse_width(pulse_width)

    def set(self):
        self.set_angle(300)

    def back(self):
        self.set_angle(0)