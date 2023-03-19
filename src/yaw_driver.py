import pyb

class Yaw():
    def __init__(self, pin):
        """!
        Brief: The initial setup for the motor that controls yaw. Sets up the pin, timer, min
        and max pulse width.
        :param pin: the pin to be used for output
        :"""
        freq = 200
        self.tim = pyb.Timer(2, freq=freq)
        self.ch = self.tim.channel(3, pyb.Timer.PWM, pin=pin)
        self.min_pulse_width = 500
        self.max_pulse_width = 2500
        self.set_angle(0)
