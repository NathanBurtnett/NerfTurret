import utime

import motor_driver
import pyb
import encoder_reader

yaw_encoder = encoder_reader.EncoderReader(pyb.Pin.board.PC6, pyb.Pin.board.PC7, 8)
yaw_encoder.zero()

yaw_motor = motor_driver.MotorDriver(pyb.Pin.board.PA10, pyb.Pin.board.PB4,
                        pyb.Pin.board.PB5, 3)



responses = []

acc_max = 0
yaw_motor.set_duty_cycle(80)
ts = utime.ticks_ms()

yaw_encoder.zero()
yaw_encoder.read()
v_last = 0

tl = utime.ticks_us()
while utime.ticks_ms() - ts < 5000 and yaw_encoder.read() < 10000:
    dt = (utime.ticks_us() - tl) / 1e6 # sec
    yaw_encoder.read()
    d = yaw_encoder.delta()

    if d == 0:
        continue

    v = yaw_encoder.delta() / dt
    acc = (v - v_last) / dt
    acc_max = max(acc, acc_max)
    v_last = v

yaw_motor.set_duty_cycle(0)

print(acc_max)
