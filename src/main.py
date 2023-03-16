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
import cotasks

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

main_button = pyb.Pin(pyb.Pin.board.PB3, pyb.Pin.IN, pull=pyb.Pin.PULL_UP)


if __name__ == "__main__":
    # Create motor and encoder objects
    fire = ts.Share('l', thread_protect=False, name="Servo Actuation Flag")
    yaw_control = ts.Share('f', thread_protect=False, name="Input to yaw mode")
    yaw_mode = ts.Share('l', thread_protect=False, name="Yaw mode control") # Controls what mode yaw is in. 0=position, 1=position move finished, 2 = raw PWM control
    speed = ts.Share('l', thread_protect=False, name="Flywheel Base Speed")
    errory = ts.Share('f', thread_protect=False, name="Camera y Error")
    buzzer = ts.Share('l', thread_protect=False, name="Speaker Sound")
    cam_control_flag = ts.Share('l', thread_protect=False, name="Camera Control")

    task_list = ct.TaskList()
    yawTask = ct.Task(cotasks.yaw, name="Yaw Motor Driver", priority=1,
                      period=10, profile=False, trace=False,
                      shares=(yaw_control, yaw_mode))
    task_list.append(yawTask)
    flywheelTask = ct.Task(cotasks.flywheel, name="Flywheel Motor Driver", priority=1,
                           period=10, profile=True, trace=False,
                           shares=(speed, errory))
    task_list.append(flywheelTask)
    firingTask = ct.Task(cotasks.firing_pin, name="Firing Servo Controller", priority=2,
                         period=300, profile=True, trace=False,
                         shares=fire)
    task_list.append(firingTask)
    cameraTask = ct.Task(cotasks.camera, name="Camera Controller", priority=1,
                         period=1000/30, profile=False, trace=False,
                         shares=(yaw_control, yaw_mode, cam_control_flag, errory, fire))
    task_list.append(cameraTask)

    fire.put(0)
    cam_control_flag.put(0)
    start_time = time.ticks_ms()
    fire_time = start_time + 5000
    state = 0
    speed.put(0)

    print("SETUP COMPLETE! Starting... Press button to home.")

    while main_button.value():
        task_list.pri_sched()

    # Homing routine
    yaw_mode.put(cotasks.YAW_HOME)
    yaw_control.put(settings.home_speed)

    while yaw_mode.get() != cotasks.YAW_RESET:
        task_list.pri_sched()

    print("HOME DONE!")

    yaw_mode.put(cotasks.YAW_POSITION)
    yaw_control.put(settings.yaw_home)

    while yaw_mode.get() != cotasks.YAW_POSITION_SETTLED:
        task_list.pri_sched()

    print("Homed! Starting control FSM. Press button to begin the duel!")

    state = 0

    while True:
        task_list.pri_sched()
        current_time = time.ticks_ms()

        if state == 0:  # Preform a home on button press
            state = 1

        elif state == 1:  # IDLE
            # print("IDLE")
            speed.put(0)
            if not main_button.value():
                print("GOING INTO PRE-ACTIVE!!")
                start_time = time.ticks_ms()
                state = 2

        elif state == 2:  # PRE-ACTIVATE
            # print("PRE-ACTIVE")
            speed.put(settings.arm_percent)

            if time.ticks_ms() - start_time > settings.pre_arm_time:
                print("GOING INTO ACTIVE!!")
                start_time = time.ticks_ms()
                state = 3
                yaw_mode.put(cotasks.YAW_POSITION)
                yaw_control.put(settings.yaw_active)


        elif state == 3:  # ACTIVATE
            # print("ACTIVE")
            speed.put(settings.fire_percent)
            if yaw_mode.get() == cotasks.YAW_POSITION_SETTLED and time.ticks_ms() - start_time > settings.track_delay:
                print("GOING INTO TRACKING!!")
                cam_control_flag.put(1)
                yaw_mode.put(cotasks.YAW_RAW_PWM)
                state = 4

        elif state == 4:  # POSITION
            if cam_control_flag.get() == 0:
                print("GOING INTO FIRE MODE!!")
                cam_control_flag.put(0)
                yaw_mode.put(cotasks.YAW_IDLE)
                start_time = utime.ticks_ms()
                state = 5

        elif state == 5: # FIRE
            fire.put(1)
            if utime.ticks_ms() - start_time > 5000:
                yaw_mode.put(cotasks.YAW_POSITION)
                yaw_control.put(settings.yaw_home)
                fire.put(0)
                state = 6

        elif state == 6:  # RETURN
            if yaw_mode.get() == cotasks.YAW_POSITION_SETTLED:
                yaw_mode.put(cotasks.YAW_IDLE)
                yaw_control.put(0)
                state = 1

