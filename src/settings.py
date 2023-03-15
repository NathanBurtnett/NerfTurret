pre_arm_time = 1000

# Flywheel settings
fire_percent = 45
arm_percent = 40
max_ramp = 10  # % / second

# Yaw settings
yaw_p = .1
yaw_i = .001
yaw_d = 0  # .0000015
yaw_settle_err = 200

# Pitch settings
pitch_factor = 0.01

enc_per_deg = 16384 / 360
gearRatio = 200 / 27
deg_fac = enc_per_deg * gearRatio
yaw_active = 200 * deg_fac
yaw_home = 20 * deg_fac

home_speed = -90
