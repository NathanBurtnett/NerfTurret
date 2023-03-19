import pyb

class Servo:
    def __init__(self, pin):
        """!
        Brief: The initial setup for the servo motor that controls the firing mechanism.
        Sets up the pin, timer, min and max pulse width.
        :param pin: the pin to be used for output
        :"""
        self.tim = pyb.Timer(2, freq=200)
        self.ch = self.tim.channel(3, pyb.Timer.PWM, pin=pin)
        self.min_pulse_width = 500
        self.max_pulse_width = 2500
        self.is_set = False

    def set_angle(self, angle):
        """!
        Brief: Changes the input angle into a pulse width to be sent to the servo
        :param angle: the angle to be changed into a pulse width for motor actuation
        :return: The pulse width percentage"""
        pulse_width = int((angle) / 180.0 * (self.max_pulse_width - self.min_pulse_width) + self.min_pulse_width)
        self.ch.pulse_width(pulse_width*100)

    def set(self):
        """!
        Brief: Sets the servo angle to be 120, used to bump the projectile into the flywheels
        :return: The set angle for the servo and True for code to know that the servo is in firing position"""
        self.set_angle(120)
        self.is_set = True

    def back(self):
        """!
        Brief: Sets the servo angle to be 75, used to retract the arm from the projectile
        :return: The set angle for the servo and False for code to know that the machine is retraced
        from the projectile"""
        self.set_angle(75)
        self.is_set = False
