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

# i2c_bus = I2C(1, freq = 1000000)
# # Select MLX90640 camera I2C address, normally 0x33, and check the bus
# scanhex = [f"0x{addr:X}" for addr in i2c_bus.scan()]
# print(f"I2C Scan: {scanhex}")
#
# # Create the camera object and set it up in default mode
#
# gc.collect()
# print(f"Free Mem: {gc.mem_free()}")
# cam = MLX_Cam(i2c_bus)
# gc.collect()
# print(f"Free Mem: {gc.mem_free()}")
# cam._camera.refresh_rate(2)

 def yaw(shares):
     instructions = shares
     state = 0
     yawmotor = MotorDriver(pyb.Pin.board.PA10, pyb.Pin.board.PB4, pyb.Pin.board.PB5, 3)
     yawencoder = EncoderReader(pyb.Pin.board.PB6, pyb.Pin.board.PB7, 4)
     yawkp = 5
     yawki = .5
     yawkd = .01
     deg2enc = 44.4444
     while True:
         con = Control(yawkp, yawki, yawkd, yawsetpoint, initial_output=0)
         if instructions.get() == 1:
             state = 1
             instructions.put(0)
         elif state == 1:
             # Turn 180
             measured_output = EncoderReader.read()
             setpoint = con.set_setpoint(180*deg2enc)
             con.run(setpoint, measured_output)
             state = 2
         elif state == 2:
             # Adjust via the camera
             pass
         
#
#
#     if state.get() >= 2:
#         while True:
#             con = Control(kp.get(), ki.get(), kd.get(), setpoint.get(), initial_output=0)
#
#             while reset.get() == 0:
#                 con.set_setpoint(setpoint.get())
#                 con.set_Kp(kp.get())
#                 con.set_Ki(ki.get())
#                 con.set_Kd(kd.get())
#
#                 measured_output = -enc0.read()
#                 motor_actuation = con.run(setpoint.get(), measured_output)
#                 m0.set_duty_cycle(motor_actuation)
#
#                 data.put(measured_output)
#                 yield 0
#
#         yield 0

# def flywheel(shares):
#     state, speed, throttle = shares
#     flywheel = Flywheel(pyb.Pin.board.PB3)
#     if state >= 3: #ERROR CORRECTION
#         flywheel.set_percent(throttle)
#     yield 0

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


def firing_pin(shares):
    instructions = shares
    state = 0
    servo = Servo(pyb.Pin.board.PB10)
    while True:
        #Check State via Instructions
        if instructions.get() == 1:
            state = 1
            instructions.put(0)
        elif state == 1: # Fire
            servo.set()
            state = 2
        elif state == 2: # Delay
            ctime = time.ticks_ms()
            if ctime + 500 <= time.ticks_ms():
                state = 3
        elif state == 3: # Return
            servo.back()
            state = 0

            current_time = time.ticks_ms()

        yield 0



if __name__ == "__main__":

    #Create motor and encoder objects
    state = ts.Share('l', thread_protect = False, name = "FSM State Var")
    yawsetpoint = ts.Share('l', thread_protect = False, name = "Yaw Motor setpoint")
    yawkp = ts.Share('l', thread_protect = False, name = "Yaw Motor setpoint")
    throttle = ts.Share('f', thread_protect = False, name = "Flywheel Throttle")
    pitch = ts.Share('f', thread_protect = False, name = "Flywheel Pitch")

    #Setup tasks
    task_list = ct.TaskList()
    # yawTask = ct.Task(yaw, name="Yaw Motor Driver", priority=1,
    #                   period=1000, profile=True, trace=False,
    #                   shares=(state, yawsetpoint))
    # task_list.append(yawTask)
    cameraTask = ct.Task(camera, name="Camera Controller", priority=2,
                         period=2000, profile=False, trace=False,
                         shares=(state, yawsetpoint, cam))
    task_list.append(cameraTask)
    #
    # flywheelTask = ct.Task(flywheel, name="Flywheel Motor Driver", priority=1,
    #                        period=1000, profile=True, trace=False,
    #                        shares=(state, pitch, throttle))
    # task_list.append(flywheelTask)
    #
    # firingTask = ct.Task(firing_pin, name="Firing Servo Controller", priority=1,
    #                      period=2000, profile=True, trace=False,
    #                      shares=(state))
    # task_list.append(firingTask)

    while True:
        task_list.pri_sched()