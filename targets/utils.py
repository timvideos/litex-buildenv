import pprint


def csr_map_update(csr_map, csr_peripherals):
    csr_map.update(dict((n, v)
        for v, n in enumerate(csr_peripherals, start=max(csr_map.values()) + 1)))


def csr_map_update_print(csr_map, csr_peripherals):
    print()
    print("-"*75)
    print("Previous Max: {}".format(max(csr_map.values())))
    csr_map.update(dict((n, v)
        for v, n in enumerate(csr_peripherals, start=max(csr_map.values()) + 1)))
    print("     New Max: {}".format(max(csr_map.values())))
    csr_values = list((b,a) for a, b in csr_map.items())
    csr_values.sort()
    pprint.pprint(csr_values)
    print("-"*75)
    print()
