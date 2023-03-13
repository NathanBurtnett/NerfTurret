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
        kp = .05
        ki = .175
        kd = .000001
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
        return motor_actuation

def tune(self, position, error):
    # simulate a process with a delay and some noise
    return input_signal + 0.1 * (2 * random.random() - 1)
    # initialize PID controller gains
    Kp = 0.0
    Ki = 0.0
    Kd = 0.0
    # initialize tuning parameters
    Ku = 1.0
    Tu = 1.0
    alpha = 0.5
    # initialize error and error integral
    #error = 0.0
    error_integral = 0.0
    # initialize loop variables
    last_time = time.time()
    last_error = 0.0
    motor_actuation = 0.0
    # loop until the controller is tuned
    while Kp == 0.0 or Ki == 0.0 or Kd == 0.0:
        # calculate the elapsed time since the last loop iteration
        current_time = time.time()
        delta_time = current_time - last_time
        # read the current input signal from the process function
        input_signal = process_function(output_signal)
        # calculate the error and error integral
        error = input_signal - output_signal
        error_integral += error * delta_time
        # calculate the derivative term
        if delta_time > 0:
            error_derivative = (error - last_error) / delta_time
        else:
            error_derivative = 0.0
        # calculate the output signal
        output_signal = Kp * error + Ki * error_integral + Kd * error_derivative

        # update last error and last time
        last_error = error
        last_time = current_time

        # perform the Ziegler-Nichols tuning method
        if output_signal > Ku:
            if Kp == 0.0:
                Kp = alpha * Ku / output_signal
            elif Ki == 0.0:
                Ki = 1.2 * Kp * Tu / (alpha * Tu + 2 * delta_time)
            elif Kd == 0.0:
                Kd = 0.5 * Kp * alpha * Tu / (alpha * Tu + delta_time)

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
        return motor_actuation