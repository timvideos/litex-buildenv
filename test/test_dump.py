#!/usr/bin/env python3
from litex.soc.tools.remote import RemoteClient

rom_base = 0x00000000
dump_size = 0x8000
words_per_packet = 128

wb = RemoteClient()
wb.open()

# # #

print("dumping cpu rom to dump.bin...")
dump = []
for n in range(dump_size//(words_per_packet*4)):
    dump += wb.read(rom_base + n*words_per_packet*4, words_per_packet)
f = open("dump.bin", "wb")
for v in dump:
    f.write(v.to_bytes(4, byteorder="big"))
f.close()

# # #

wb.close()
