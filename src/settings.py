import math

do_rotate = True

pre_arm_time = 1000

# Flywheel settings
fire_percent = 100
arm_percent = 45
max_ramp = 10  # % / second

# Yaw settings
yaw_p = .8
yaw_i = .01
yaw_d = .007  # .0000015
yaw_settle_err = 40

# Yaw Velocity
yaw_v_p = 10
yaw_v_i = .05
yaw_v_d = 0

# track X settings
tx_p = 6
tx_i = .012
tx_d = .3
tx_settle_d = 1
tx_settle_e = .3
off_x = -1.75
track_delay = 5000


# Pitch settings
pitch_factor = -0.1

enc_per_deg = 4072 / 360
gearRatio = 200 / 16
deg_fac = enc_per_deg * gearRatio

yaw_max = 250 * deg_fac
yaw_min = 20 * deg_fac

yaw_active = 195 * deg_fac # 185 * deg_fac
yaw_home = 5 * deg_fac

home_speed = -20


def linearize(actuation):
    """!
    @brief: This function takes in the motor actuation term created from the control file
    and puts the value through a linearization function for PID control use.

    @param: actuation: The motor actuation used for PID control through PWM

    return: The corrected motor actuation."""
    sign = abs(actuation) / actuation if actuation != 0 else 1
    a = abs(actuation)

    a1 = 15
    m1 = 35

    if a < a1:
        a = (a / a1) * m1
    else:
        a = max(a, m1)

    return a * sign

