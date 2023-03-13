"""!
@file control.py
This file contains the P controller used to drive the motor
to a position
"""
import pyb
import utime


class Control:
    """!
    The class used for the controller of the motor. This class sets up
    initial conditions of the motor, calculates the error between
    current position and desired position, and returns the motor effort.
    """
    def __init__(self, Kp, Ki, Kd, setpoint, initial_output):
        """!
        The initial state of the controller. Sets up the initial conditions of the
        passed through motor
        :param Kp: The proportional controller gain for the motor, used to determine
        the motor effort.
        :param setpoint: The desired position of the encoder that was set.
        :param initial_output: The initial position of the passed through device
        """
        self.t_start = utime.ticks_ms()
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
        self.t_prev = 0
        self.deg2enc = 16384 / 360
        self.gearRatio = 200 / 27

    def run(self, measured_output):
        """!
        Calculates the error between the current encoder position and the desired
        encoder position and returns the motor effort.
        :param setpoint: The desired position of the encoder that was set.
        :param measured_output: The measured position of the encoder
        :return: The motor effort
        """
        print(f"Setpoint: {self.setpoint}")
        error = self.setpoint - measured_output
        if self.t_prev == 0:
            self.t_prev = self.t_start
        t = utime.ticks_ms()
        #print(f"Previous Time: {self.t_prev }")
        #print(f"Current Time: {t}")
        self.Kp_control = self.Kp * error
        self.Ki_control += self.Ki * error * (t - self.t_prev)
        if self.t_prev != t:
            self.Kd_control = self.Kd * (error - self.error_prev) / (t - self.t_prev)
        else:
            self.Kd_control = 0
        self.error_prev = error
        self.t_prev = t
        motor_actuation = self.Kp_control + self.Ki_control + self.Kd_control
        return motor_actuation

    def set_setpoint(self, setpoint):
        """!
        Sets the value of setpoint to be part of self.
        """
        deg = setpoint * self.deg2enc * self.gearRatio
        self.setpoint = deg

    def track(self, errorin):
        error = errorin
        t = utime.ticks_ms()
        # Setup track specific Kp, Ki, Kd
        kp = 5
        ki = .8
        kd = .00009
        kp_con = 0
        ki_con = 0
        kd_con = 0
        # Calculate Kp, Ki, Kd
        kp_con = kp * error
        ki_con += ki * error * (t - self.t_prev)
        if self.t_prev != t:
            kd_con = kd * (error - self.error_prev) / (t - self.t_prev)
        else:
            kd_con = 0
        # # set Previous error and time variables
        self.error_prev = error
        self.t_prev = t
        motor_actuation = kp_con + ki_con + kd_con
        print(f"motor actuation {motor_actuation}")
        return motor_actuation

    # def tune(self, position, poserror):
    #     t = utime.time()
    #     self.kptuned = 0
    #     self.kituned = 0
    #     self.kdtuned = 0
    #     I = 0
    #
    #     dt = (t-self.tprev)
    #
    #     P = self.kptuned * poserror
    #     I += self.kituned * poserror * dt
    #     if self.t_prev != t:
    #         D = self.kdtuned * (poserror - self.error_prev) / dt
    #     else:
    #         D = 0
    #
    #     out = P + I + D
    #
    #     self.error_prev
    #
    #     if self.Ku == 0
    #         self.kptuned += dt*10^(-3)
    #         if abs(poserror) < abs(self.error_prev) and self.error_prev < 0:
    #             self.Ku = self.kptuned / (4* abs(self.error_prev))
    #             self.Tu = dt * 4
    #             self.kptuned = 0
    #
    #     else:
    #         self.kptuned = 0.6 * self.Ku
    #         self.kituned = 1.2 * self.Ku / self.Tu
    #         self.kdtuned = 0.075 * self.Ku * self.Tu
    #
    #     print(self.kptuned)
    #     print(self.kituned)
    #     print(self.kdtuned)
    #     print(self.Ku)
    #     print(self.Tu)
