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


def main(wb):
    wb.open()
    regs = wb.regs
    # # #
    for i in range(16):
        regs.leds_out.write(i)
        time.sleep(0.1)

    rgb_leds = [RGBLed(regs, "rgb_leds", i) for i in range(4)]
    for led in rgb_leds:
        for c in "rgb":
            pwm = getattr(led, c)
            pwm.enable()
            for i in range(64):
                pwm.configure(128, i)
                time.sleep(0.001)
            pwm.disable()
    # # #
    wb.close()
