"""!
@file main.py

@brief Automated Nerf turret control using STM32 Nucleo, Micropython, and a thermal camera.

This script controls an automated Nerf turret using PID control for the motors and a thermal camera
to process images. The camera calculates the centroid of the center of mass and passes the data
through UART to the STM32 Nucleo board, which runs Micropython and the pyboard library.

@author Nathan Burtnett, Jacob Agar, Dominic Chmiel
@date 2/23/2023
"""

# Imports
import pyb
import cotask as ct
import task_share as ts
from encoder_reader import EncoderReader
from control import Control
from motor_driver import MotorDriver
from servo_driver import Servo
from flywheel_driver import Flywheel
import utime as time

"""!
Pin Layout

PA10: Motor Driver Enable Pin
PB8: Flywheel 1 PWM TIM4_CH3
PB9: Flywheel 2 PWM TIM4_CH4
PB4: Motor Driver IN1PIN
PB5: Motor Driver IN2PIN
PC6: Encoder Pin A
PC7: Encoder Pin B
PA0: Uart TX
PA1: Uart RX
PB10: Servo PWM 
"""

def yaw(shares):
    """!
    @brief Controls the yaw motor and encoder for the Nerf turret.

    This function manages the yaw motor's movement using PID control,
    ensuring that it does not turn past its initial starting point (0 degrees)
    and 270 degrees past that, no matter what value of yawcon.

    @param shares Tuple containing shared variables for x-axis error and yaw control state.
    """
    errorx, yawcon = shares
    yawmotor = MotorDriver(pyb.Pin.board.PA10, pyb.Pin.board.PB4, pyb.Pin.board.PB5, 3)
    yawencoder = EncoderReader(pyb.Pin.board.PC6, pyb.Pin.board.PC7, 8)
    kp = .0675
    ki = .0000015
    kd = .0000015
    yawmotor.set_duty_cycle(0)
    con = Control(kp, ki, kd, setpoint=0, initial_output=0)
    con.set_setpoint(0)
    yawencoder.zero()

    deg2enc = 16384 / 360
    gearRatio = 200 / 27
    min_enc = 0
    max_enc = 270 * deg2enc * gearRatio

    while True:
        measured_output = yawencoder.read()
        motor_actuation = 0
        yield 0

        if min_enc <= measured_output <= max_enc:
            if yawcon.get() == 1:  # Turn 180
                con.set_setpoint(180)
                motor_actuation = con.run(measured_output)
                if -1 < motor_actuation < 1:
                    yawcon.put(3)
                    yield 0
            elif yawcon.get() == 2:  # back to start
                con.set_setpoint(0)
                motor_actuation = con.run(measured_output)
                if -1 < motor_actuation < 1:
                    yawcon.put(0)
                    yield 0
            elif yawcon.get() == 3:  # Track
                motor_actuation = con.track(errorx.get())

        yawmotor.set_duty_cycle(motor_actuation)
        yield 0

def flywheel(shares, pitch_factor=0.2):
    """!
    @brief Controls the speed of the flywheel motors and adjusts pitch based on y-axis error.

    This function handles the speed and pitch of the flywheel motors using the y-axis error
    from the thermal camera. It applies a differential speed to the motors, causing the Nerf
    ball to pitch up or down based on the error.

    @param shares Tuple containing shared variables for flywheel base speed and y-axis error.
    @param pitch_factor Scaling factor to control the pitch adjustment based on y-axis error.
    """
    speedperc, errory = shares
    flywheelL = Flywheel(pyb.Pin.board.PB8, 4, 3)
    flywheelU = Flywheel(pyb.Pin.board.PB9, 4, 4)
    while True:
        base_speed = speedperc.get()
        pitch = pitch_factor * errory.get()

        upper_speed = base_speed * (1 + pitch)
        lower_speed = base_speed * (1 - pitch)

        flywheelU.set_percent(upper_speed)
        flywheelL.set_percent(lower_speed)
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

def button_callback():
    """!
    @brief Toggles the button_pressed flag and prints the state change message.

    This callback function changes the state of the button_pressed flag when the button is
    pressed. It also prints a message to indicate the change in state.
    """
    global button_pressed

    button_pressed = not button_pressed
    print("Button Toggle", "On" if button_pressed else "Off")

# Create and configure the button
button = pyb.Switch()
button_pressed = False
button.callback(button_callback)

if __name__ == "__main__":
    # Create motor and encoder objects
    fire = ts.Share('l', thread_protect=False, name="Servo Actuation Flag")
    fire.put(0)
    yawcon = ts.Share('l', thread_protect=False, name="Turn 180 Flag")  # [1: Turn 180] [2: Turn -180]
    yawcon.put(0)
    speed = ts.Share('l', thread_protect=False, name="Flywheel Base Speed")
    errorx = ts.Share('f', thread_protect=False, name="Camera x Error")
    errory = ts.Share('f', thread_protect=False, name="Camera y Error")
    buzzer = ts.Share('l', thread_protect=False, name="Speaker Sound")

    task_list = ct.TaskList()
    yawTask = ct.Task(yaw, name="Yaw Motor Driver", priority=1,
                      period=30, profile=False, trace=False,
                      shares=(errorx, yawcon))
    task_list.append(yawTask)
    flywheelTask = ct.Task(flywheel, name="Flywheel Motor Driver", priority=1,
                           period=10, profile=True, trace=False,
                           shares=(speed, errory))
    task_list.append(flywheelTask)
    firingTask = ct.Task(firing_pin, name="Firing Servo Controller", priority=2,
                         period=200, profile=True, trace=False,
                         shares=fire)
    task_list.append(firingTask)
    cameraTask = ct.Task(camera, name="Camera Controller", priority=1,
                         period=1000/30, profile=False, trace=False,
                         shares=(errorx, errory))
    task_list.append(cameraTask)

    start_time = time.ticks_ms()
    fire_time = start_time + 5000
    tuning_mode = False
    tuning_state = 0
    shot = 0

    while True:
        task_list.pri_sched()
        current_time = time.ticks_ms()

        if button_pressed:
            tuning_mode = not tuning_mode

        if tuning_mode:
            # Implement tuning mode UI
            # ...
        else:
            # Implement turret state machine
            if yawcon.get() == 0:
                if button_pressed:
                    yawcon.put(1)
                    speed.put(75)
            elif yawcon.get() == 3:
                if -0.1 < errorx.get() < 0.1 and shot == 0:
                    fire.put(1)
                    shot = 1
                if current_time >= fire_time and shot == 1:
                    fire.put(1)
                    shot = 2
                if current_time >= fire_time + 2000:
                    yawcon.put(2)
