from migen.fhdl.std import *
from migen.sim.generic import run_simulation
from migen.flow.actor import EndpointDescription

from gateware.encoder.buffer import EncoderBuffer
from gateware.csc.test.common import *


class TB(Module):
    def __init__(self):
        stream_description = EndpointDescription([("data", 128)], packetized=True)

        self.submodules.streamer = PacketStreamer(stream_description)
        self.submodules.streamer_randomizer = AckRandomizer(stream_description, 50)
        self.submodules.buffer = EncoderBuffer()
        self.submodules.logger_randomizer = AckRandomizer(stream_description, 50)
        self.submodules.logger = PacketLogger(stream_description)
        self.comb += [
        	Record.connect(self.streamer.source, self.streamer_randomizer.sink),
            Record.connect(self.streamer_randomizer.source, self.buffer.sink),
            Record.connect(self.buffer.source, self.logger_randomizer.sink),
            Record.connect(self.logger_randomizer.source, self.logger.sink)
        ]

    def check_pixel(self, value, index, block):
        line = block[index//8]
        reference = (line >> 16*(7-index%8)) & 0xffff
        return value == reference

    def gen_simulation(self, selfp):
        # create 8x8 blocks (one 8 pixels line per stb)
        blocks = []
        for i in range(8):
            block = [randn(2**128) for line in range(8)]
            blocks.append(block)

        # send blocks
        for block in blocks:
            packet = Packet(block)
            self.streamer.send(packet)

        # receive the 8x8 blocks (1 pixel per stb)
        errors = 0
        for block in blocks:
            yield from self.logger.receive()
            for index, value in enumerate(self.logger.packet):
                errors += not self.check_pixel(value, index, block)
        print("blocks: {}, errors: {}".format(len(blocks), errors))

if __name__ == "__main__":
    run_simulation(TB(), ncycles=2048, vcd_name="my.vcd", keep_files=True)
