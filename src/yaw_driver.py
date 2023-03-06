import pyb

class Yaw():
    def __init__(self, pin):
        freq = 200
        self.tim = pyb.Timer(2, freq=freq)
        self.ch = self.tim.channel(3, pyb.Timer.PWM, pin=pin)
        self.min_pulse_width = 500
        self.max_pulse_width = 2500
        self.set_angle(0)
