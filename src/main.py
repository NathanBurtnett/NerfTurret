"""!
@file main.py

@author Nathan Burtnett, Jacob Agar, Dominic Chmiel
@date 2/23/2023
"""

import pyb
import sys
import utime
import cotask as ct
import task_share as ts
from machine import Pin, I2C
from encoder_reader import EncoderReader
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
    k_p = 0.1  # Proportional gain
    k_i = 0.001  # Integral gain
    integral_error = 0
    prev_error = 0

    while True:
        if state.get() >= 2:
            # Calculate error
            error = yawsetpoint.get() - yawencoder.read()

            # Calculate integral error
            integral_error += error

            # Calculate control output
            control_output = k_p * error + k_i * integral_error

            # Set motor speed
            yawmotor.set_percent(control_output)

            # Save previous error
            prev_error = error

        yield 0

def flywheel(shares):
    state, pitch = shares
    flywheel = Flywheel(pyb.Pin.board.PB3)
    if state >= 3: #ERROR CORRECTION
        flywheel.set_percent(pitch)
    yield 0


def camera(shares):
    yawencoder = EncoderReader(pyb.Pin.board.PB6, pyb.Pin.board.PB7, 4)
    state, yawsetpoint = shares
    i2c_address = 0x33
    i2c_bus = I2C(1)
    camera = MLX_Cam(i2c_bus)

    if state >= 3:
        # Get the camera image and calculate the error between the center of the image
        # and the current yaw position
        image = camera.get_image()
        image_center_x = image.shape[1] // 2
        yaw_position = yawencoder.get_count() / yawencoder.get_resolution() * 360.0
        error = image_center_x - yaw_position

        # Update the yaw setpoint by adding the error to the current setpoint
        yawsetpoint.put(yawsetpoint.get() + error)
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

def master_mind(shares):
    state, yawsetpoint, throttle, pitch = shares

    # Constants
    THROTTLE_TOLERANCE = 0.05
    YAW_KP = 0.1
    YAW_KD = 0.01

    # Variables
    yaw_error = 0
    yaw_error_last = 0

    # Main loop
    while True:

        # State 0: Initialize all components
        if state.get() == 0:
            # Initialize camera and flywheel motor
            camera.init()
            throttle.put(0.0)
            state.put(1)

        # State 1: Wait for button press signal
        elif state.get() == 1:
            # Wait for button press signal
            if button_pressed():
                state.put(2)

        # State 2: Rotate 180, arm flywheels
        elif state.get() == 2:
            # Rotate turret 180 degrees
            yawsetpoint.put(180)
            utime.sleep_ms(1000) # Wait for rotation to complete

            # Arm flywheel motor
            throttle.put(0.9)
            state.put(3)

        # State 3: Aim turret at bright spot, correct flywheel speed
        elif state.get() == 3:
            # Get camera image
            image = camera.get_image()

            # Find brightest spot in image
            brightest_spot = find_brightest_spot(image)

            # Calculate yaw error
            yaw_error_last = yaw_error
            yaw_error = 180 - brightest_spot[0] # Yaw error is the distance from the center of the image

            # Calculate yawsetpoint
            yawsetpoint.put(int(yawsetpoint.get() + yaw_error * YAW_KP + (yaw_error - yaw_error_last) * YAW_KD))

            # Correct flywheel speed
            if abs(brightest_spot[1] - 255 / 2) > 20:
                throttle.put(throttle.get() + THROTTLE_TOLERANCE * (brightest_spot[1] - 255 / 2))

        # State 4: Fire
        elif state.get() == 4:
            # Fire the gun
            firing_pin.fire()

            # Return to state 2
            state.put(2)

        # State 5: Rotate 180, go to state 0
        elif state.get() == 5:
            # Rotate turret 180 degrees
            yawsetpoint.put(0)
            utime.sleep_ms(1000) # Wait for rotation to complete

            # Reset flywheel motor
            throttle.put(0.0)

            # Go back to state 0
            state.put(0)

        # State 10: Demo mode
        elif state.get() == 10:
            # Rotate turret 180 degrees
            yawsetpoint.put(180)
            utime.sleep_ms(1000) # Wait for rotation to complete

            # Arm flywheel motor
            throttle.put(0.9)
            utime.sleep_ms(5000) # Wait for flywheel to reach speed

            # Fire the gun
            firing_pin.fire()
            utime.sleep_ms(1000) # Wait for firing to complete

            # Rotate turret 180 degrees
            yawsetpoint.put(0)
            utime.sleep_ms(1000) # Wait for rotation to complete

            # Reset flywheel motor
            throttle.put(0.0)





if __name__ == "__main__":

    #Create motor and encoder objects
    state = ts.Share('l', thread_protect = False, name = "FSM State Var")
    yawsetpoint = ts.Share('l', thread_protect = False, name = "Yaw Motor setpoint")
    throttle = ts.Share('f', thread_protect = False, name = "Flywheel Throttle")
    pitch = ts.Share('f', thread_protect = False, name = "Flywheel Pitch")

    #Setup tasks
    task_list = ct.TaskList()
    yawTask = ct.Task(yaw(), name="Yaw Motor Driver", priority=1,
                      period=100, profile=True, trace=False,
                      shares=(state, yawsetpoint))
    task_list.append(yawTask)

    cameraTask = ct.Task(camera(), name="Camera Controller", priority=1,
                         period=100, profile=True, trace=False,
                         shares=(state, yawsetpoint))
    task_list.append(cameraTask)

    flywheelTask = ct.Task(flywheel(), name="Flywheel Motor Driver", priority=1,
                           period=100, profile=True, trace=False,
                           shares=(state, pitch, yawsetpoint))
    task_list.append(flywheelTask)

    firingTask = ct.Task(firing_pin(), name="Firing Servo Controller", priority=1,
                         period=100, profile=True, trace=False,
                         shares=(state, yawsetpoint))
    task_list.append(firingTask)

    mastermindTask = ct.Task(master_mind(), name="Mastermind", priority=2,
                             period=100, profile=True, trace=False,
                             shares=(state, yawsetpoint, throttle, pitch))
    task_list.append(mastermindTask)

    state.put(10)
    while True:
        task_list.pri_sched()