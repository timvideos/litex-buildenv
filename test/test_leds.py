#!/usr/bin/env python3
from litex.soc.tools.remote import RemoteClient

import time


class PWM:
    def __init__(self, regs, name):
        for reg in ["enable", "period", "width"]:
            setattr(self, "_" + reg, getattr(regs, name + "_" + reg))
        self.set_period(128)
        self.set_width(0)
        self.enable()

    def enable(self):
        self._enable.write(1)

    def disable(self):
        self._enable.write(0)

    def set_period(self, period):
        self._period.write(period)

    def set_width(self, width):
        self._width.write(width)


class RGBLed:
    def __init__(self, regs, name, n):
        for c in "rgb":
            self.r = PWM(regs, "rgb_leds_r"+str(n))
            self.g = PWM(regs, "rgb_leds_g"+str(n))
            self.b = PWM(regs, "rgb_leds_b"+str(n))


wb = RemoteClient()
wb.open()
regs = wb.regs

# # #

for i in range(16):
    regs.leds_out.write(i)
    time.sleep(0.1)

rgb_leds = [RGBLed(regs, "rgb_leds", i) for i in range(4)]

def knight_rider(color, value):
    sequence = []
    sequence = [0, 1, 2, 3, 2, 1, 0, 1, 2, 3]
    for led in sequence:
        pwm = getattr(rgb_leds[led], color)
        pwm.set_width(value)
        time.sleep(0.05)
        pwm.set_width(0)

def disco():
    for led in rgb_leds:
        for c in "rgb":
            pwm = getattr(led, c)
            for i in range(64):
                pwm.set_width(i)
                time.sleep(0.005)
            pwm.set_width(0)

knight_rider("r", 64)
time.sleep(0.5)
knight_rider("r", 64)
time.sleep(0.5)

disco()


# # #

wb.close()
