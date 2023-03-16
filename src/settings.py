import math

do_rotate = False

pre_arm_time = 1000

# Flywheel settings
fire_percent = 45
arm_percent = 45
max_ramp = 10  # % / second

# Yaw settings
yaw_p = .09
yaw_i = .001
yaw_d = 0  # .0000015
yaw_settle_err = 200

# track X settings
tx_p = 8
tx_i = .01 #.0001
tx_d = 0#.00000003
tx_settle_d = 1
tx_settle_e = 1
off_x = 3.5
# Pitch settings
pitch_factor = 0.01

enc_per_deg = 16384 / 360
gearRatio = 200 / 27
deg_fac = enc_per_deg * gearRatio

yaw_max = 250 * deg_fac
yaw_min = 20 * deg_fac

yaw_active = 200 * deg_fac
yaw_home = 20 * deg_fac

home_speed = -90
# def linearize(actuation):
#     if actuation == 0:
#         return 0
#
#     return abs(actuation) / actuation * (20 + 20 * math.pow(abs(actuation),  .3))

def linearize(actuation):
    return abs(actuation) / actuation * max(abs(actuation), 26)