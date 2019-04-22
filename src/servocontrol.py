import time

import Adafruit_PCA9685
import RPi.GPIO as GPIO


class PTZServo(object):
    def __init__(self):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)

        # # power-up servo controller
        GPIO.setup(18, GPIO.OUT)
        GPIO.output(18, 0)
        self.pwm = Adafruit_PCA9685.PCA9685()
        self.pwm.set_pwm_freq(60)

    def set_position(self, servo, position):
        self.pwm.set_pwm(servo, 0, position)
        # True
