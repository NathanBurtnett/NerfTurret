"""!
@file main.py

@author Nathan Burtnett, Jacob Agar, Dominic Chmiel
@date 2/23/2023
"""

import pyb
import sys
import cotask as ct
import task_share as ts
from encoder_reader import EncoderReader
from control import Control
from motor_driver import MotorDriver
from servo_driver import Servo
from flywheel_driver import Flywheel
from mlx_cam import MLX_Cam
import gc
import utime as time
from machine import Pin, I2C
from mlx90640 import MLX90640, RefreshRate, REGISTER_MAP
from mlx90640.calibration import NUM_ROWS, NUM_COLS, IMAGE_SIZE, TEMP_K
from mlx90640.image import ChessPattern, InterleavedPattern, ProcessedImage
from mlx90640.regmap import CameraInterface


"""!
Pin Layout

PA_10: Motor Driver Enable Pin

PA_2: Flywheel 1 PWM TIM2_CH3
PB_3: Flywheel 2 PWM TIM2_CH2
PB_4: Motor Driver IN1PIN
PB_5: Motor Driver IN2PIN
PB_6: Encoder Pin A
PB_7: Encoder Pin B
PB_8: I2C SCL Camera
PB_9: I2C SDA Camera
PB_10: Servo PWM 
"""

def yaw(shares):
    yawsetpoint, yawcon = shares
    yawmotor = MotorDriver(pyb.Pin.board.PA10, pyb.Pin.board.PB4, pyb.Pin.board.PB5, 3)
    yawencoder = EncoderReader(pyb.Pin.board.PB6, pyb.Pin.board.PB7, 4)
    yawkp = 5
    yawki = .5
    yawkd = .01
    deg2enc = 44.4444
    while True:
         con = Control(yawkp, yawki, yawkd, yawsetpoint)
         if yawcon.get() == 1: # Turn 180
             measured_output = yawencoder.read()
             motor_actuation = con.run(180*deg2enc, measured_output)
             yawmotor.set_duty_cycle(motor_actuation)
             yawcon.put(0)
         elif yawcon.get() == 2: # Turn -180
             measured_output = yawencoder.read()
             motor_actuation = con.run(180 * deg2enc, measured_output)
             yawmotor.set_duty_cycle(motor_actuation)
             yawcon.put(0)
         elif yawcon.get() == 3: # Track

         yield 0

def flywheel(shares):
    speed, pitch = shares
    speed.put(1000)
    pitch.put(1)
    flywheelU = Flywheel(pyb.Pin.board.PB3)
    flywheelL = Flywheel(pyb.Pin.board.PA2)
    #Arm Flywheels
    while True:
        flywheelU.set_speed(speed)
        flywheelL.set_speed(speed*pitch)
        yield 0

def firing_pin(shares):
    fire = shares
    state = 0
    servo = Servo(pyb.Pin.board.PB10)
    while True:
        if fire.get() == 1: # Fire
            servo.set()
            state = 1
            fire.put(0)
            ctime = time.ticks_ms()
        if state == 1: # Delay
            if ctime + 1000 <= time.ticks_ms():
                state = 2
        elif state == 2: # Return
            servo.back()
            state = 0
        yield 0

# def camera(shares):
#     state, yawsetpoint, cam = shares
#
#     if state >= 3:
#         # Get the camera image and calculate the error between the center of the image
#         # and the current yaw position
#         print("Click.", end='')
#         begintime = time.ticks_ms()
#         image = cam.get_image()
#         print(f" {time.ticks_diff(time.ticks_ms(), begintime)} ms")
#
#         # Find the row index and column index of the pixel with the greatest value
#         max_pixel = max((val, (i, j)) for i, row in enumerate(image) for j, val in enumerate(row))
#         row_idx, col_idx = max_pixel[1]
#
#         # Calculate the vertical center of the screen
#         center_row = len(image) // 2
#
#         # Calculate the error in pixels
#         error_pixels = abs(row_idx - center_row)
#
#         # Convert the error in pixels to encoder counts
#         camera_width_degrees = 55
#         encoder_counts = 65535
#         pixel_size_degrees = camera_width_degrees / len(image[0])
#         error_degrees = error_pixels * pixel_size_degrees
#         error = round(error_degrees / camera_width_degrees * encoder_counts)
#
#         # Update the yaw setpoint by adding the error to the current setpoint
#         yawsetpoint.put(error)
#         print(error)
#     pass

if __name__ == "__main__":
    #Create motor and encoder objects
    fire = ts.Share('l', thread_protect=False, name="Servo Actuation Flag")
    fire.put(0)
    yawcon = ts.Share('l', thread_protect=False, name="Turn 180 Flag") #[1: Turn 180] [2: Turn -180]
    yawcon.put(0)
    speed = ts.Share('l', thread_protect=False, name="Flywheel Base Speed"
    pitchPerc = ts.Share('l', thread_protect=False, name="Flywheel Differential Perfentage")
    yawsetpoint = ts.Share('l', thread_protect = False, name = "Yaw Motor setpoint")

    #Setup tasks
    task_list = ct.TaskList()
    yawTask = ct.Task(yaw, name="Yaw Motor Driver", priority=1,
                      period=1000, profile=False, trace=False,
                      shares=(yawsetpoint,turn))
    task_list.append(yawTask)
    flywheelTask = ct.Task(flywheel, name="Flywheel Motor Driver", priority=1,
                           period=100, profile=True, trace=False,
                           shares=(speed,pitchPerc))
    task_list.append(flywheelTask)
    firingTask = ct.Task(firing_pin, name="Firing Servo Controller", priority=1,
                         period=100, profile=True, trace=False,
                         shares=fire)
    task_list.append(firingTask)
    # cameraTask = ct.Task(camera, name="Camera Controller", priority=2,
    #                      period=2000, profile=False, trace=False,
    #                      shares=(state, yawsetpoint, cam))
    # task_list.append(cameraTask)
    while True:
        task_list.pri_sched()