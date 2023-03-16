import pyb
import utime
from encoder_reader import EncoderReader
from control import Control
from motor_driver import MotorDriver
from servo_driver import Servo
from flywheel_driver import Flywheel
import utime as time
import settings

YAW_IDLE = 0
YAW_RESET = 1
YAW_POSITION = 2
YAW_POSITION_SETTLED = 3
YAW_RAW_PWM = 4
YAW_HOME = 5

def yaw(shares):
    """!
    @brief Controls the yaw motor and encoder for the Nerf turret.

    This function manages the yaw motor's movement using PID control,
    ensuring that it does not turn past its initial starting point (0 degrees)
    and 270 degrees past that, no matter what value of yawcon.

    @param shares Tuple containing shared variables for x-axis error and yaw control state.
    """
    yaw_control, yaw_mode = shares

    yaw_motor = MotorDriver(pyb.Pin.board.PA10, pyb.Pin.board.PB4, pyb.Pin.board.PB5, 3)
    yaw_motor.set_duty_cycle(0)

    yaw_encoder = EncoderReader(pyb.Pin.board.PC6, pyb.Pin.board.PC7, 8)
    yaw_encoder.zero()

    con = Control(settings.yaw_p, settings.yaw_i, settings.yaw_d, setpoint=0, initial_output=0, settled_d_thresh=5, settled_e_thresh=200)
    con.set_setpoint(0)

    vel_con = Control(settings.yaw_v_p, settings.yaw_v_i, settings.yaw_v_d, setpoint=0, initial_output=0, settled_d_thresh=5, settled_e_thresh=200)
    con.set_setpoint(0)

    home_start = None
    last_t = utime.ticks_ms()

    while True:

        measured_output = yaw_encoder.read()
        t = utime.ticks_ms()
        delta_t = t - last_t
        motor_actuation = 0

        # 0 = IDLE
        if yaw_mode.get() == YAW_IDLE:
            motor_actuation = 0

        elif yaw_mode.get() == YAW_RESET:  # DISABLE
            yaw_encoder.zero()
            motor_actuation = 0

        elif yaw_mode.get() == YAW_POSITION or yaw_mode.get() == YAW_POSITION_SETTLED:  # POSITIONAL CONTROL
            con.set_setpoint(yaw_control.get())
            motor_actuation = con.run(measured_output)
            # print("ERR", con.error_prev)
            if con.is_settled():
                yaw_mode.put(YAW_POSITION_SETTLED)
            else:
                yaw_mode.put(YAW_POSITION)

        elif yaw_mode.get() == YAW_RAW_PWM:  # PWM CONTROL
            motor_actuation = yaw_control.get()

        # SOFT ENDSTOPS FOR MODES 0-3
        # if measured_output > settings.yaw_max and motor_actuation > 0:
        #     motor_actuation = 0
        # elif measured_output < settings.yaw_min and motor_actuation < 0:
        #     motor_actuation = 0

        # HOME
        if yaw_mode.get() == YAW_HOME:  # HOME
            home_start = home_start or utime.ticks_ms()
            vel_con.set_setpoint(yaw_control.get())
            motor_actuation = vel_con.run(yaw_encoder.delta() / delta_t)

            print("HOME", yaw_encoder.delta(), motor_actuation, utime.ticks_ms() - home_start)

            if yaw_encoder.delta() == 0 and utime.ticks_ms() - home_start > 1000:
                home_start = None
                yaw_encoder.zero()
                yaw_mode.put(YAW_RESET)

        yaw_motor.set_duty_cycle(motor_actuation)

        last_t = t
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

        flywheelU.set_percent(base_speed)
        flywheelL.set_percent(base_speed)

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
    while True:
        if fire.get() == 1 and servo.is_set:
            servo.back()
        elif fire.get() == 1 and not servo.is_set:
            servo.set()
        else:
            servo.back()
        yield 0

def camera(shares):
    """!
    @brief Controls the communication with the thermal camera and processes the centroid data.

    This function manages communication with the thermal camera through UART. It reads the
    centroid data (x and y errors) and processes the received data. Invalid or out-of-range
    values are handled to prevent unexpected behavior.

    @param shares Tuple containing shared variables for x-axis and y-axis errors.
    """
    yaw_control, yaw_mode, cam_control_flag, errory, fire_flag = shares
    cam = pyb.UART(4, 115200, timeout=0)

    con = Control(settings.tx_p, settings.tx_i, settings.tx_d, 0, 0, settled_e_thresh=settings.tx_settle_e, settled_d_thresh=settings.tx_settle_d)

    res = ""
    while True:
        if cam.any():
            c = chr(cam.readchar())
            if c != "\n":
                res += c
                continue

            try:
                # Parse the response and split by comma
                # print(res)
                x, y = res.strip().split(',')
                x, y = float(x), float(y)

                if cam_control_flag.get() == 1:
                    act = con.run(-x + settings.off_x)
                    print("CAM CON", con.error, con.error_dot)
                    print("ACT", act)
                    yaw_mode.put(YAW_RAW_PWM)
                    yaw_control.put(act)

                    if con.is_settled():
                        fire_flag.put(1)
                        cam_control_flag.put(0)
                    else:
                        fire_flag.put(0)

                errory.put(y)

            except ValueError:
                pass

            res = ""

        yield 0
