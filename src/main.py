"""!
@file main.py

@author Nathan Burtnett, Jacob Agar, Dominic Chmiel
@date 2/23/2023
"""

import pyb
import sys
import utime as time
import cotask as ct
import task_share as ts
from machine import Pin, I2C
from mlx90640 import MLX90640, RefreshRate, REGISTER_MAP
from mlx90640.calibration import NUM_ROWS, NUM_COLS, IMAGE_SIZE, TEMP_K
from mlx90640.image import ChessPattern, InterleavedPattern, ProcessedImage
from mlx90640.regmap import CameraInterface
from encoder_reader import EncoderReader
from control import Control
from motor_driver import MotorDriver
from servo_driver import Servo
from flywheel_driver import Flywheel
from mlx_cam import MLX_Cam


"""!
State Machine

state 0: Initialize all componants
state 1: Wait for button press signal
state 2: Rotate 180, arm flywheels
state 3: Aim turret at bright spot, correct flywheel speed
state 4: Fire
state 5: Rotate 180 go to state 0
"""

"""!
Pin Layout

PA_10: Motor Driver Enable Pin

PB_3: Flywheel PWM TIM2_CH2
PB_4: Motor Driver IN1PIN
PB_5: Motor Driver IN2PIN
PB_6: Encoder Pin A
PB_7: Encoder Pin B
PB_8: I2C SCL Camera
PB_9: I2C SDA Camera
PB_10: Servo PWM 
"""


def yaw(shares):
    state, yawsetpoint = shares
    yawmotor = MotorDriver(pyb.Pin.board.PA10, pyb.Pin.board.PB4, pyb.Pin.board.PB5, 3)
    yawencoder = EncoderReader(pyb.Pin.board.PB6, pyb.Pin.board.PB7, 4)

    while True:
        con = Control(kp.get(), setpoint.get(), initial_output=0)
    k_p = 0.1  # Proportional gain
    k_i = 0.001  # Integral gain
    integral_error = 0
    prev_error = 0

    if state.get() >= 2:
        # Set motor speed
        yawmotor.set_percent(control_output)

        yield 0

def flywheel(shares):
    state, speed, throttle = shares
    flywheel = Flywheel(pyb.Pin.board.PB3)
    if state >= 3: #ERROR CORRECTION
        flywheel.set_percent(throttle)
    yield 0

def camera(shares):
    state, yawsetpoint = shares
    try:
        from pyb import info
    # Oops, it's not an STM32; assume generic machine.I2C for ESP32 and others
    except ImportError:
        # For ESP32 38-pin cheapo board from NodeMCU, KeeYees, etc.
        i2c_bus = I2C(1, scl=Pin(22), sda=Pin(21))
    # OK, we do have an STM32, so just use the default pin assignments for I2C1
    else:
        i2c_bus = I2C(1,  freq=1_000_000)
    # Select MLX90640 camera I2C address, normally 0x33, and check the bus
    scanhex = [f"0x{addr:X}" for addr in i2c_bus.scan()]
    print(f"I2C Scan: {scanhex}")

    # Create the camera object and set it up in default mode
    cam = MLX_Cam(i2c_bus)
    MLX90640.refresh_rate.setter(0b010)

    if state >= 3:
        # Get the camera image and calculate the error between the center of the image
        # and the current yaw position
        print("Click.", end='')
        begintime = time.ticks_ms()
        image = cam.get_image()
        print(f" {time.ticks_diff(time.ticks_ms(), begintime)} ms")

        # Find the row index and column index of the pixel with the greatest value
        max_pixel = max((val, (i, j)) for i, row in enumerate(image) for j, val in enumerate(row))
        row_idx, col_idx = max_pixel[1]

        # Calculate the vertical center of the screen
        center_row = len(image) // 2

        # Calculate the error in pixels
        error_pixels = abs(row_idx - center_row)

        # Convert the error in pixels to encoder counts
        camera_width_degrees = 55
        encoder_counts = 65535
        pixel_size_degrees = camera_width_degrees / len(image[0])
        error_degrees = error_pixels * pixel_size_degrees
        error = round(error_degrees / camera_width_degrees * encoder_counts)

        # Update the yaw setpoint by adding the error to the current setpoint
        yawsetpoint.put(error)
        print(error)
    pass


def firing_pin(shares):
    state = shares
    servo = pyb.Servo(pyb.Pin.board.PB10)
    if state == 5: #state 5 is fire mode
        servo.set()
    elif state == 10: #DEMO
        servo.set()
    else:
        servo.back()
    yield 0


if __name__ == "__main__":

    #Create motor and encoder objects
    state = ts.Share('l', thread_protect = False, name = "FSM State Var")
    yawsetpoint = ts.Share('l', thread_protect = False, name = "Yaw Motor setpoint")

    throttle = ts.Share('f', thread_protect = False, name = "Flywheel Throttle")
    pitch = ts.Share('f', thread_protect = False, name = "Flywheel Pitch")

    #Setup tasks
    task_list = ct.TaskList()
    yawTask = ct.Task(yaw, name="Yaw Motor Driver", priority=1,
                      period=1000, profile=True, trace=False,
                      shares=(state, yawsetpoint))
    task_list.append(yawTask)

    cameraTask = ct.Task(camera, name="Camera Controller", priority=2,
                         period=1000, profile=True, trace=False,
                         shares=(state, yawsetpoint))
    task_list.append(cameraTask)

    flywheelTask = ct.Task(flywheel, name="Flywheel Motor Driver", priority=1,
                           period=1000, profile=True, trace=False,
                           shares=(state, pitch, throttle))
    task_list.append(flywheelTask)

    firingTask = ct.Task(firing_pin, name="Firing Servo Controller", priority=1,
                         period=1000, profile=True, trace=False,
                         shares=(state, yawsetpoint))
    task_list.append(firingTask)

    state.put(10)
    while True:
        task_list.pri_sched()