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
    yaw_control = ts.Share('f', thread_protect=False, name="Input to yaw mode")
    yaw_mode = ts.Share('l', thread_protect=False, name="Yaw mode control") # Controls what mode yaw is in. 0=position, 1=position move finished, 2 = raw PWM control
    speed = ts.Share('l', thread_protect=False, name="Flywheel Base Speed")
    errorx = ts.Share('f', thread_protect=False, name="Camera x Error")
    errory = ts.Share('f', thread_protect=False, name="Camera y Error")
    buzzer = ts.Share('l', thread_protect=False, name="Speaker Sound")

    task_list = ct.TaskList()
    yawTask = ct.Task(cotasks.yaw, name="Yaw Motor Driver", priority=1,
                      period=10, profile=False, trace=False,
                      shares=(errorx, yaw_control, yaw_mode))
    task_list.append(yawTask)
    flywheelTask = ct.Task(cotasks.flywheel, name="Flywheel Motor Driver", priority=1,
                           period=10, profile=True, trace=False,
                           shares=(speed, errory))
    task_list.append(flywheelTask)
    firingTask = ct.Task(cotasks.firing_pin, name="Firing Servo Controller", priority=2,
                         period=200, profile=True, trace=False,
                         shares=fire)
    task_list.append(firingTask)
    cameraTask = ct.Task(cotasks.camera, name="Camera Controller", priority=1,
                         period=1000/30, profile=False, trace=False,
                         shares=(errorx, errory))
    task_list.append(cameraTask)

    start_time = time.ticks_ms()
    fire_time = start_time + 5000
    state = 0
    speed.put(0)

    print("SETUP COMPLETE! Starting... Press button to home.")

    while not button_pressed:
        task_list.pri_sched()

    # Homing routine
    yaw_mode.put(4)
    yaw_control.put(-75)
    button_pressed = False

    while yaw_mode.get() != 0:
        task_list.pri_sched()

    yaw_mode.put(2)
    yaw_control.put(settings.yaw_home)
    while yaw_mode.get() != 0:
        task_list.pri_sched()

    print("Homed! Starting control FSM. Press button to begin the duel!")

    button_pressed = False
    while True:
        task_list.pri_sched()
        current_time = time.ticks_ms()

        if state == 0:  # Preform a home on button press
            state = 1

        elif state == 1:  # IDLE
            # print("IDLE")
            speed.put(0)
            if button_pressed:
                print("GOING INTO PRE-ACTIVE!!")
                start_time = time.ticks_ms()
                button_pressed = False
                state = 2

        elif state == 2:  # PRE-ACTIVATE
            #print("PRE-ACTIVE")
            speed.put(settings.arm_percent)

            if time.ticks_ms() - start_time > settings.pre_arm_time:
                state = 3
                yaw_mode.put(2)
                yaw_control.put(settings.yaw_active)

        elif state == 3:  # ACTIVATE
            # print("ACTIVE")
            speed.put(settings.fire_percent)
            if yaw_mode.get() == 0:
                # Slew to 180 finished.
                state = 4

        elif state == 4:  # TRACK
            if button_pressed:
                button_pressed = False
                print("TRK ERR", errory.get(), errorx.get())
                yaw_mode.put(2)
                yaw_control.put(settings.yaw_home)
                state = 6

        elif state == 5:  # FIRE
            pass

        elif state == 6:  # RETURN
            if yaw_mode.get() == 0:
                state = 1

