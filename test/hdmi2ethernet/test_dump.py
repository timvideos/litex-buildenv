import copy
import png

SDRAM_BASE = 0x40000000
LINE_SIZE = 1280*3
DUMP_SIZE = 1280*720*4
WORDS_PER_PACKET = 128

def chunks(l, n):
    for i in xrange(0, len(l), n):
        yield l[i:i+n]

def extract_rgb(pixel):
    b = (pixel & 0x3ff)/4
    pixel = pixel >> 10
    g = (pixel & 0x3ff)/4
    pixel = pixel >> 10
    r = (pixel & 0x3ff)/4
    return r, g, b

def main(wb):
    wb.open()
    regs = wb.regs
    # # #
    print("dumping framebuffer memory...")
    dump = []
    for n in range(DUMP_SIZE//(WORDS_PER_PACKET*4)):
        data = wb.read(SDRAM_BASE + n*WORDS_PER_PACKET*4, WORDS_PER_PACKET)
        for pixel in data:
            dump += extract_rgb(pixel)
    dump = [dump[x:x+LINE_SIZE] for x in range(0, len(dump), LINE_SIZE)]
    print("dumping to png file...")
    png.from_array(dump, "RGB").save("dump.png")
    # # #
    wb.close()
