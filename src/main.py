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

def yaw(shares):
    if state == 0:  # INTIALIZE
        yawmotor= MotorDriver(pyb.Pin.board.PA10, pyb.Pin.board.PB4, pyb.Pin.board.PB5, 3)
        yawencoder = EncoderReader(pyb.Pin.board.PB6, pyb.Pin.board.PB7, 4)

    yield 0

def flywheel(shares):
    state, pitch = shares
    if state == 0: #INTIALIZE
        flywheel_upper = Flywheel(pyb.Pin.board.PB3)
        flywheel_lower = Flywheel(pyb.Pin.board.PB10)

    elif state == 2: #ARMING
        flywheel_upper.arm()
        flywheel_lower.arm()

    elif state == 3: #ERROR CORRECTION
        flywheel_upper.set_percent(pitch)
        flywheel_lower.set_percent(pitch)
    yield 0

def camera(shares):

    pass

def firing_pin(shares):
    state = shares
    servo = Servo(pyb.Pin.board.PB4)
    if state == 5: #state 5 is fire mode
        servo.set()
        state = 4
    else:
        servo.back()
    yield 0

def master_mind(shares):


if __name__ == "__main__":

    #Create motor and encoder objects
    state = ts.Share('l', thread_protect = False, name = "FSM State Var")
    yawKp = ts.Share('f', thread_protect = False, name = "Yaw Motor Kp")
    yawsetpoint = ts.Share('l', thread_protect = False, name = "Yaw Motor setpoint")
    throttle = ts.Share('f', thread_protect = False, name = "Flywheel Throttle")
    pitch = ts.Share('f', thread_protect = False, name = "Flywheel Pitch")

    #Setup tasks
    task_list = ct.TaskList()
    yawTask = ct.Task(yaw(), name = "Yaw Motor Driver", priority=1,
                      period = 100, profile = True, trace = False,
                      shares = (state))
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
    mastermindTask = ct.Task(master_mind(), name="Firing Servo Controller", priority=2,
                         period=100, profile=True, trace=False,
                         shares=(state))
    task_list.append(mastermindTask)

    state = 0
    while True:
        task_list.pri_sched()