import time

class PTZServo(object):
    def __init__(self):
        print("PTZServoFake: GPIO.setwarnings(False)")
        print("PTZServoFake: GPIO.setmode(GPIO.BCM)")

        # # power-up servo controller
        print("PTZServoFake: GPIO.setup(18, GPIO.OUT)")
        print("PTZServoFake: GPIO.output(18, 0)")
        print("PTZServoFake: self.pwm = Adafruit_PCA9685.PCA9685()")
        print("PTZServoFake: self.pwm.set_pwm_freq(60)")

    def set_position(self, servo, position):
        print("PTZServoFake: self.pwm.set_pwm({}, 0, {})".format(servo, position))
        # True
