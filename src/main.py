"""!
@file main.py

@author Nathan Burtnett, Jacob Agar, Dominic Chmiel
@date 2/23/2023
"""

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

PA_10: Motor Driver Enable Pin
PB8: Flywheel 1 PWM TIM4_CH3
PB9: Flywheel 2 PWM TIM4_CH4
PB_4: Motor Driver IN1PIN
PB_5: Motor Driver IN2PIN
PC_6: Encoder Pin A
PC_7: Encoder Pin B
PA0: Uart TX
PA1: Uart RX
PB_10: Servo PWM 
"""

def yaw(shares):
    errorx, yawcon = shares
    yawmotor = MotorDriver(pyb.Pin.board.PA10, pyb.Pin.board.PB4, pyb.Pin.board.PB5, 3)
    yawencoder = EncoderReader(pyb.Pin.board.PC6, pyb.Pin.board.PC7, 8)
    kp = .0675
    ki = .0000015
    kd = .0000015
    yawmotor.set_duty_cycle(0)
    con = Control(kp, ki, kd, setpoint = 0, initial_output=0)
    con.set_setpoint(0)
    yawencoder.zero()
    while True:
        measured_output = yawencoder.read()
        motor_actuation = 0
        yield 0
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
        # print(f"Motor Position: {measured_output}")
        # print(f"Motor Actuation: {motor_actuation}")
        yawmotor.set_duty_cycle(motor_actuation)
        yield 0

def flywheel(shares):
    speedinput, errory = shares
    flywheelL = Flywheel(pyb.Pin.board.PB8, 4, 3)
    flywheelU = Flywheel(pyb.Pin.board.PB9, 4, 4)
    while True:
        #print(speedinput.get())
        flywheelU.set_speed(speedinput.get())
        flywheelL.set_speed(speedinput.get())
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
            if ctime + 150 <= time.ticks_ms():
                state = 2
        elif state == 2:  # Return
            servo.back()
            state = 0
        yield 0

def camera(shares):
    errorx, errory = shares
    cam = pyb.UART(4, 115200, timeout=0)
    while True:
        if cam.any():
            response = cam.readline()
            #print("raw", response)
            error = response.decode().strip().split(',')
            if len(error) != 2:
                #print("Invalid response format:", response)
                continue  # ignore invalid response and continue
            try:
                if abs(float(error[0])) < 16:
                    errorx.put(float(error[0]))
                if abs(float(error[1])) < 12:
                    errory.put(float(error[1]))
            except ValueError:
                #print("Invalid value in response:", response)
                continue  # ignore invalid value and continue
        yield 0


button = pyb.Switch()
button_pressed = False
def button_callback():
    global button_pressed
    if button_pressed:
        print("Button Toggle Off")
        button_pressed = False
    else:
        print("Button Toggle On")
        button_pressed = True
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
                      period=20, profile=False, trace=False,
                      shares=(errorx, yawcon))
    task_list.append(yawTask)
    flywheelTask = ct.Task(flywheel, name="Flywheel Motor Driver", priority=1,
                           period=10, profile=True, trace=False,
                           shares=(speed, errory))
    task_list.append(flywheelTask)
    firingTask = ct.Task(firing_pin, name="Firing Servo Controller", priority=1,
                         period=100, profile=True, trace=False,
                         shares=fire)
    task_list.append(firingTask)
    cameraTask = ct.Task(camera, name="Camera Controller", priority=1,
                         period=1000/30, profile=False, trace=False,
                         shares=(errorx, errory))
    task_list.append(cameraTask)

    start_time = time.ticks_ms()
    fire_time = start_time + 3000
    yawcon.put(3)
    while True:
        task_list.pri_sched()
        current_time = time.ticks_ms()

        # Main Duel Checks
        if button_pressed:
        #     yawcon.put(1)
            # print("Flywheel On")
            speed.put(5)
        elif not button_pressed:
            # print("Flywheel Off")
            speed.put(2)
        if current_time >= fire_time:
            if .5 > errorx.get() > -.5:
                fire.put(1)
            fire_time = current_time + 1000
        # if current_time >= fire_time + 1000:
        #     yawcon.put(2)
        #     speed.put(1000)
        #     button.put(0)

        # if current_time >= fire_time:
        #     fire.put(1)
        #     fire_time = fire_time + 400  # set fire_time to infinity to prevent further execution
        # if current_time >= speed_time:
        #     speed.put(1200)
        #     speed_time = float('inf')  # set speed_time to infinity to prevent further execution