"""!
@file control.py
This file contains the P controller used to drive the motor
to a position
"""
import pyb
import utime
import math
import settings

# Converts 0-100 into a "real" 0-100 to control actual motor movement



class Control:
    """!
    The class used for the controller of the motor. This class sets up
    initial conditions of the motor, calculates the error between
    current position and desired position, and returns the motor effort.
    """
    def __init__(self, Kp, Ki, Kd, setpoint, initial_output, settled_e_thresh=.5, settled_d_thresh=.2):
        """!
        The initial state of the controller. Sets up the initial conditions of the
        passed through motor
        :param Kp: The proportional controller gain for the motor, used to determine
        the motor effort.
        :param setpoint: The desired position of the encoder that was set.
        :param initial_output: The initial position of the passed through device
        """
        self.Kp = Kp
        self.Kp_control = 0
        self.Ki = Ki
        self.Ki_control = 0
        self.Kd = Kd
        self.Kd_control = 0
        self.Ku = 0
        self.Tu = 0
        self.setpoint = setpoint
        self.output = initial_output
        self.times = []
        self.positions = []
        self.error_prev = 0

        self.t_prev = utime.ticks_ms()
        self.t = utime.ticks_ms()
        self.delta_t = 0

        self.delta_error = 0
        self.error = 0
        self.error_dot = 0

        self.settled_e_thresh = settled_e_thresh
        self.settled_d_thresh = settled_d_thresh

    def run(self, measured_output):
        """!
        Calculates the error between the current encoder position and the desired
        encoder position and returns the motor effort.
        :param setpoint: The desired position of the encoder that was set.
        :param measured_output: The measured position of the encoder
        :return: The motor effort
        """
        self.t = utime.ticks_ms()

        self.error = self.setpoint - measured_output
        self.delta_error = self.error - self.error_prev
        self.delta_t = self.t - self.t_prev

        # Handle cases where this controller is reused after a period
        if self.delta_t > 100:
            self.Ki_control = 0
            self.delta_t = 0

        self.error_dot = 1000 * (self.error - self.error_prev) / (self.t - self.t_prev) if self.delta_t > 0 else 0

        self.Kp_control = self.Kp * self.error

        # Anti-spool
        if -100 < self.Kp_control + self.Ki_control + self.Kp_control < 100:
            self.Ki_control += self.Ki * self.error * self.delta_t

        self.Kd_control = self.Kd * self.error_dot

        self.error_prev = self.error
        self.t_prev = self.t

        motor_actuation = self.Kp_control + self.Ki_control + self.Kd_control

        # print("PID OUT", motor_actuation, self.Kp_control, self.Ki_control, self.Kd_control)
        return settings.linearize(motor_actuation)

    def set_setpoint(self, setpoint):
        """!
        Sets the value of setpoint to be part of self.
        """
        self.setpoint = setpoint

    def is_settled(self):
        """!
        Returns the error less than the error threshold to let the machine know it is settled"""
        # print("CON_SETT", abs(self.error), abs(self.error_dot))
        return abs(self.error) < self.settled_e_thresh and abs(self.error_dot) < self.settled_d_thresh