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
import utime as time

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
    yawkp = .005
    yawki = .0005
    yawkd = .01
    yawmotor.set_duty_cycle(0)
    while True:
        con = Control(yawkp, yawki, yawkd, yawsetpoint.get(), initial_output=0)
        measured_output = yawencoder.read()
        print(f"Motor Position: {measured_output}")
        motor_actuation = con.run(measured_output)
        if yawcon.get() == 1:  # Turn 180
            print("Turning 180")
            yawencoder.zero()
            con.set_setpoint(180)
            motor_actuation = con.run(measured_output)
            yawcon.put(0)
        elif yawcon.get() == 2:  # Turn -180
            print("Turning -180")
            yawencoder.zero()
            con.set_setpoint(-180)
            motor_actuation = con.run(measured_output)
            yawcon.put(0)
        elif yawcon.get() == 3:  # Track
            pass
        print(f"Motor Actuation: {motor_actuation}")
        yawmotor.set_duty_cycle(motor_actuation)
        yield 0


def flywheel(shares):
    speedinput, pitch = shares
    speedinput.put(1000)
    pitch.put(1)
    flywheelU = Flywheel(pyb.Pin.board.PB3)
    flywheelL = Flywheel(pyb.Pin.board.PA2)
    while True:
        flywheelU.set_speed(speedinput.get())
        flywheelL.set_speed(speedinput.get() * pitch.get())
        yield 0


def firing_pin(shares):
    fire = shares
    state = 0
    servo = Servo(pyb.Pin.board.PB10)
    while True:
        if fire.get() == 1:  # Fire
            servo.set()
            state = 1
            fire.put(0)
            ctime = time.ticks_ms()
        if state == 1:  # Delay
            if ctime + 1000 <= time.ticks_ms():
                state = 2
        elif state == 2:  # Return
            servo.back()
            state = 0
        yield 0


def camera(shares):
    yawsetpoint = shares
    cam = pyb.UART(4, 115200, timeout=5000)
    while True:
        response = cam.readline()
        if response:
            fields = response.decode().strip().split(',')
        yield 0

if __name__ == "__main__":
    # Create motor and encoder objects
    fire = ts.Share('l', thread_protect=False, name="Servo Actuation Flag")
    fire.put(0)
    yawcon = ts.Share('l', thread_protect=False, name="Turn 180 Flag")  # [1: Turn 180] [2: Turn -180]
    yawcon.put(0)
    speed = ts.Share('l', thread_protect=False, name="Flywheel Base Speed")
    pitchPerc = ts.Share('l', thread_protect=False, name="Flywheel Differential Perfentage")
    yawsetpoint = ts.Share('l', thread_protect=False, name="Yaw Motor setpoint")

    task_list = ct.TaskList()
    yawTask = ct.Task(yaw, name="Yaw Motor Driver", priority=2,
                      period=10, profile=False, trace=False,
                      shares=(yawsetpoint, yawcon))
    task_list.append(yawTask)
    flywheelTask = ct.Task(flywheel, name="Flywheel Motor Driver", priority=1,
                           period=10, profile=True, trace=False,
                           shares=(speed, pitchPerc))
    task_list.append(flywheelTask)
    firingTask = ct.Task(firing_pin, name="Firing Servo Controller", priority=1,
                         period=10, profile=True, trace=False,
                         shares=fire)
    task_list.append(firingTask)
    cameraTask = ct.Task(camera, name="Camera Controller", priority=1,
                         period=10, profile=False, trace=False,
                         shares=(yawsetpoint))
    task_list.append(cameraTask)

    yawcon.put(1)
    starttime = time.ticks_ms()
    while True:
        if starttime + 5000 < time.ticks_ms():
            pass
            # speed.put(1000)
        task_list.pri_sched()
