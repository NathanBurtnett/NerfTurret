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
Enables UART communication between the STM32 and ESP32 in order to deliver error from center of the 
camera and the centroid of the thermal blob. Different gains for PID control are used to allow finer
adjustment when using the camera error.
"""
yawmotor = MotorDriver(pyb.Pin.board.PA10, pyb.Pin.board.PB4, pyb.Pin.board.PB5, 3)
yawencoder = EncoderReader(pyb.Pin.board.PC6, pyb.Pin.board.PC7, 8)
kp = .0675
ki = .0000015
kd = .0000015
yawmotor.set_duty_cycle(0)
con = Control(kp, ki, kd, setpoint = 0, initial_output=0)
con.set_setpoint(180)
yawencoder.zero()
while True:
    measured_output = yawencoder.read()
    motor_actuation = con.run(measured_output)
    yawmotor.set_duty_cycle(motor_actuation)