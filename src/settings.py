import math

do_rotate = True

pre_arm_time = 1000

# Flywheel settings
fire_percent = 0
arm_percent = 0
max_ramp = 10  # % / second

# Yaw settings
yaw_p = .2
yaw_i = .004
yaw_d = .002  # .0000015
yaw_settle_err = 40

# Yaw Velocity
yaw_v_p = 10
yaw_v_i = .05
yaw_v_d = 0

# track X settings
tx_p = 1.5
tx_i = .003
tx_d = .5
tx_settle_d = 1
tx_settle_e = 1
off_x = -2

stable_avg_delta = .25

# Pitch settings
pitch_factor = 0.01

enc_per_deg = 4072 / 360
gearRatio = 200 / 16
deg_fac = enc_per_deg * gearRatio

yaw_max = 250 * deg_fac
yaw_min = 20 * deg_fac

yaw_active = 90 * deg_fac # 185 * deg_fac
yaw_home = 5 * deg_fac

home_speed = -20
# def linearize(actuation):
#     if actuation == 0:
#         return 0
#
#     return abs(actuation) / actuation * (20 + 20 * math.pow(abs(actuation),  .3))

# def linearize(actuation):
#     return abs(actuation) / actuation * max(abs(actuation), 26)

def linearize(actuation):
    a1 = 20
    s1 = 46
    s2 = 46
    sign = abs(actuation) / actuation if actuation != 0 else 1
    a = abs(actuation)

    if a > a1:
        a = s2 + (a - a1) / (100 - a1) * (100 - s2)

    else:
        a = s1 * a / a1

    return a * sign

