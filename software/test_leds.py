from litex.soc.tools.remote import RemoteClient

import time


class PWM:
    def __init__(self, regs, name):
        for reg in ["enable", "period", "width"]:
            setattr(self, "_" + reg, getattr(regs, name + "_" + reg))

    def enable(self):
        self._enable.write(1)

    def disable(self):
        self._enable.write(0)

    def configure(self, period, width):
        self._period.write(period)
        self._width.write(width)


class RGBLed:
    def __init__(self, regs, name, n):
        for c in "rgb":
            self.r = PWM(regs, "rgb_leds_r"+str(n))
            self.g = PWM(regs, "rgb_leds_g"+str(n))
            self.b = PWM(regs, "rgb_leds_b"+str(n))


wb = RemoteClient(csr_data_width=8)
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
        pwm.enable()
        pwm.configure(128, value)
        time.sleep(0.05)
        pwm.configure(128, 0)
        pwm.disable()

def rgb_strip():
    for led in rgb_leds:
        for c in "rgb":
            pwm = getattr(led, c)
            pwm.enable()
            for i in range(64):
                pwm.configure(128, i)
                time.sleep(0.005)
            pwm.disable()

knight_rider("r", 64)
time.sleep(0.5)
knight_rider("r", 64)
time.sleep(0.5)
rgb_strip()


# # #

wb.close()
