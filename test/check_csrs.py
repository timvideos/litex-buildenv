#!/usr/bin/env python3
import sys
import csv
import pprint

print(sys.argv[1])

data = list(csv.reader(open(sys.argv[1],'r')))

bases = [x for x in data if x[0] == 'csr_base']
regs = [x for x in data if x[0] == 'csr_register']

mem_map = []
for _, name, loc, size, rw in regs:
    mem_map.append((int(loc, 16), int(size), name))
mem_map.sort()

for i, (loc, size, name) in enumerate(mem_map[:-1]):
    print("{:x} {} {}".format(loc, size, name))

    nloc, nsize, nname = mem_map[i+1]
    assert (loc + size*4) <= nloc, "{:x}+{} < {:x} ({} < {})".format(loc, size, nloc, name, nname)

    assert loc < (0xe0000000 + (2**14)*4), "{:x} {}".format(loc, name)

regs_in_base = {}
for _, name, loc, size, rw in regs:                                                             
    for _, bname, base, _, _ in bases:
        if name.startswith(bname):
            if bname not in regs_in_base:
                regs_in_base[bname] = []
            regs_in_base[bname].append((int(loc, 16), name[len(bname)+1:], int(size), rw))

for name, regs in sorted(regs_in_base.items()):
    num_regs = sum(size for loc, name, size, rw in regs)
    assert num_regs < 200
    print(name, num_regs)
