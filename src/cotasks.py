import pyb
import utime

import cotask as ct
import task_share as ts
from encoder_reader import EncoderReader
from control import Control
from motor_driver import MotorDriver
from servo_driver import Servo
from flywheel_driver import Flywheel
import utime as time
import settings
def yaw(shares):
    """!
    @brief Controls the yaw motor and encoder for the Nerf turret.

    This function manages the yaw motor's movement using PID control,
    ensuring that it does not turn past its initial starting point (0 degrees)
    and 270 degrees past that, no matter what value of yawcon.

    @param shares Tuple containing shared variables for x-axis error and yaw control state.
    """
    errorx, yaw_control, yaw_mode = shares

    yaw_motor = MotorDriver(pyb.Pin.board.PA10, pyb.Pin.board.PB4, pyb.Pin.board.PB5, 3)
    yaw_motor.set_duty_cycle(0)

    yaw_encoder = EncoderReader(pyb.Pin.board.PC6, pyb.Pin.board.PC7, 8)
    yaw_encoder.zero()

    con = Control(settings.yaw_p, settings.yaw_i, settings.yaw_d, setpoint=0, initial_output=0)
    con.set_setpoint(0)

    home_start = None

    while True:
        measured_output = yaw_encoder.read()
        motor_actuation = 0

        # 0 = IDLE
        if yaw_mode.get() == 0:
            motor_actuation = 0

        elif yaw_mode.get() == 1:  # DISABLE
            yaw_encoder.zero()
            motor_actuation = 0

        elif yaw_mode.get() == 2:  # POSITIONAL CONTROL
            con.set_setpoint(yaw_control.get())
            motor_actuation = con.run(measured_output)
            # print("ERR", con.error_prev)
            if con.is_settled():
                yaw_mode.put(0)

        elif yaw_mode.get() == 3:  # PWM CONTROL
            motor_actuation = yaw_control.get()

        elif yaw_mode.get() == 4:  # HOME
            home_start = home_start or utime.ticks_ms()
            motor_actuation = yaw_control.get()

            print("HOME", yaw_encoder.delta(), motor_actuation, utime.ticks_ms() - home_start)
            if yaw_encoder.delta() == 0 and utime.ticks_ms() - home_start > 1000:
                home_start = None
                yaw_encoder.zero()
                yaw_mode.put(0)

        yaw_motor.set_duty_cycle(motor_actuation)

        yield 0

def flywheel(shares):
    """!
    @brief Controls the speed of the flywheel motors and adjusts pitch based on y-axis error.

    This function handles the speed and pitch of the flywheel motors using the y-axis error
    from the thermal camera. It applies a differential speed to the motors, causing the Nerf
    ball to pitch up or down based on the error.

    @param shares Tuple containing shared variables for flywheel base speed and y-axis error.
    """
    speedperc, errory = shares
    flywheelL = Flywheel(pyb.Pin.board.PB8, 4, 3)
    flywheelU = Flywheel(pyb.Pin.board.PB9, 4, 4)

    while True:

        base_speed = speedperc.get()
        pitch = -settings.pitch_factor * errory.get()

        upper_speed = base_speed * (1 + pitch)
        lower_speed = base_speed * (1 - pitch)

        flywheelU.set_percent(upper_speed)
        flywheelL.set_percent(lower_speed)

        flywheelU.loop()
        flywheelL.loop()
        yield 0

def firing_pin(shares):
    """!
    @brief Controls the firing servo for the Nerf turret.

    This function manages the firing of darts by controlling the firing servo. It consists
    of three states: Fire, Delay, and Return. In the Fire state, the servo actuates to shoot
    a dart. In the Delay state, the system waits for a predefined time before transitioning
    to the Return state. In the Return state, the servo resets to its original position.

    @param shares Shared variable for the servo actuation flag.
    """
    fire = shares
    servo = Servo(pyb.Pin.board.PB10)

    state = 0  # 0: Idle, 1: Fire, 2: Delay, 3: Return

    while True:
        if fire.get() == 1 and state == 0:  # Fire
            servo.set()
            state = 1
            fire.put(0)
            ctime = time.ticks_ms()
        elif state == 1:  # Delay
            if ctime + 150 <= time.ticks_ms():
                state = 2
        elif state == 2:  # Return
            servo.back()
            state = 0

        yield 0

def camera(shares):
    """!
    @brief Controls the communication with the thermal camera and processes the centroid data.

    This function manages communication with the thermal camera through UART. It reads the
    centroid data (x and y errors) and processes the received data. Invalid or out-of-range
    values are handled to prevent unexpected behavior.

    @param shares Tuple containing shared variables for x-axis and y-axis errors.
    """
    errorx, errory = shares
    cam = pyb.UART(4, 115200, timeout=0)

    while True:
        if cam.any():
            response = cam.readline()
            # Parse the response and split by comma
            error_values = response.decode().strip().split(',')

            if len(error_values) == 2:
                try:
                    x, y = float(error_values[0]), float(error_values[1])

                    if -16 < x < 16:
                        errorx.put(x)
                    if -12 < y < 12:
                        errory.put(y)
                except ValueError:
                    # Ignore invalid values and continue
                    continue
            else:
                # Ignore invalid response format and continue
                continue

        yield 0
