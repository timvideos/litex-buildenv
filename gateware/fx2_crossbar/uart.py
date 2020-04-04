from migen import *

class FX2PHY(Module):
    def __init__(self, fx2_sink, fx2_source):
        self.sink, self.source = fx2_sink, fx2_source
