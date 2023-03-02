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
from encoder_reader import EncoderReader
from motor_driver import MotorDriver
from servo_driver import Servo
from flywheel_driver import Flywheel


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
    yawmotor= MotorDriver(pyb.Pin.board.PA10, pyb.Pin.board.PB4, pyb.Pin.board.PB5, 3)
    yawencoder = EncoderReader(pyb.Pin.board.PB6, pyb.Pin.board.PB7, 4)

    yield 0

def flywheel(shares):
    state, pitch = shares
    flywheel = Flywheel(pyb.Pin.board.PB3)

    if state == 3: #ERROR CORRECTION
        flywheel.set_percent(pitch)
    if state == 10:  # DEMO
        flywheel.set_percent(pitch)
    yield 0

def camera(shares):

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



if __name__ == "__main__":

    #Create motor and encoder objects
    state = ts.Share('l', thread_protect = False, name = "FSM State Var")
    yawsetpoint = ts.Share('l', thread_protect = False, name = "Yaw Motor setpoint")
    throttle = ts.Share('f', thread_protect = False, name = "Flywheel Throttle")
    pitch = ts.Share('f', thread_protect = False, name = "Flywheel Pitch")

    #Setup tasks
    task_list = ct.TaskList()
    yawTask     = ct.Task(yaw(), name = "Yaw Motor Driver", priority=1,
                      period = 100, profile = True, trace = False,
                      shares = (state,yawsetpoint))
    task_list.append(yawTask)
    flywheelTask = ct.Task(flywheel(), name="Flywheel Motor Driver", priority=1,
                      period=100, profile=True, trace=False,
                      shares=(state,pitch))
    task_list.append(flywheelTask)
    cameraTask = ct.Task(camera(), name="Camera Controller", priority=1,
                      period=100, profile=True, trace=False,
                      shares=(state))
    task_list.append(cameraTask)
    firingTask = ct.Task(firing_pin(), name="Firing Servo Controller", priority=1,
                         period=100, profile=True, trace=False,
                         shares=(state))
    task_list.append(firingTask)
    mastermindTask = ct.Task(master_mind(), name="Mastermind", priority=2,
                         period=100, profile=True, trace=False,
                         shares=(state,yawsetpoint,throttle,pitch))
    task_list.append(mastermindTask)

    state.put(10)
    while True:
        if state == 10:

            pass
        task_list.pri_sched()