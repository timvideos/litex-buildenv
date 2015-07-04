import copy

SDRAM_BASE = 0x40000000
TEST_SIZE  = 1024*1024
WORDS_PER_PACKET = 128

def seed_to_data(seed, random=True):
    if random:
        return (seed * 0x31415979 + 1) & 0xffffffff
    else:
        return seed


def check(p1, p2):
    p1 = copy.deepcopy(p1)
    p2 = copy.deepcopy(p2)
    if isinstance(p1, int):
        return 0, 1, int(p1 != p2)
    else:
        if len(p1) >= len(p2):
            ref, res = p1, p2
        else:
            ref, res = p2, p1
        shift = 0
        while((ref[0] != res[0]) and (len(res) > 1)):
            res.pop(0)
            shift += 1
        length = min(len(ref), len(res))
        errors = 0
        for i in range(length):
            if ref.pop(0) != res.pop(0):
                errors += 1
        return shift, length, errors


def generate_packet(seed, length):
    r = []
    for i in range(length):
        r.append(seed_to_data(seed, False))
        seed += 1
    return r, seed

def main(wb):
    wb.open()
    regs = wb.regs
    # # #
    errors = 0
    print("writing...")
    seed = 0
    for n in range(TEST_SIZE//(WORDS_PER_PACKET *4)):
        data, seed = generate_packet(seed, WORDS_PER_PACKET)
        wb.write(SDRAM_BASE + n*WORDS_PER_PACKET *4, data)
    print("reading...")
    seed = 0
    for n in range(TEST_SIZE//(WORDS_PER_PACKET *4)):
        ref, seed = generate_packet(seed, WORDS_PER_PACKET )
        data = wb.read(SDRAM_BASE + n*WORDS_PER_PACKET *4, WORDS_PER_PACKET)
        s, l, e = check(ref, data)
        errors += e
    print("errors: " + str(errors))
    # # #
    wb.close()
