from migen.fhdl.std import *
from migen.bank.description import *

from misoclib.com import gpio

from gateware.pwm import PWM


class ClassicLed(gpio.GPIOOut):
    def __init__(self, pads):
        gpio.GPIOOut.__init__(self, pads)


class RGBLed(Module, AutoCSR):
    def __init__(self, pads):
        nleds = flen(pads.r)

        # # #

        for n in range(nleds):
            for c in "rgb":
                setattr(self.submodules, c+str(n), PWM(getattr(pads, c)[n]))
