from migen import *
from litex.soc.interconnect.csr import CSRStatus


def _get_rw_functions(reg_name, reg_base, nwords, busword, read_only):
    r = ""

    r += "#define CSR_"+reg_name.upper()+"_ADDR "+hex(reg_base)+"\n"
    r += "#define CSR_"+reg_name.upper()+"_SIZE "+str(nwords)+"\n"
    r += "#define CSR_"+reg_name.upper()+"_RO "+str(int(read_only))+"\n"
    return r


def get_csr_header(regions, constants):
    r = "#ifndef __GENERATED_CSR_H\n#define __GENERATED_CSR_H\n"
    for name, origin, busword, obj in regions:
        origin = origin & 0x7fffffff
        if isinstance(obj, Memory):
            r += "#define "+name.upper()+"_BASE "+hex(origin)+"\n"
        else:
            r += "\n/* "+name+" */\n"
            r += "#define "+name.upper()+"_BASE "+hex(origin)+"\n"
            for csr in obj:
                nr = (csr.size + busword - 1)//busword
                r += _get_rw_functions(name + "_" + csr.name, origin, nr, busword, isinstance(csr, CSRStatus))
                origin += 4*nr

    r += "\n/* constants */\n"
    for name, value in constants:
        r += "#define " + name
        if value is not None:
            r += " " + str(value)
        r += "\n"

    r += "\n#endif\n"
    return r


def get_csr_csv(csr_regions=None, constants=None, memory_regions=None):
    r = ""

    if csr_regions is not None:
        for name, origin, busword, obj in csr_regions:
            r += "csr_base,{},0x{:08x},,\n".format(name, origin)

        for name, origin, busword, obj in csr_regions:
            if not isinstance(obj, Memory):
                for csr in obj:
                    nr = (csr.size + busword - 1)//busword
                    r += "csr_register,{}_{},0x{:08x},{},{}\n".format(name, csr.name, origin, nr, "ro" if isinstance(csr, CSRStatus) else "rw")
                    origin += 4*nr

    if constants is not None:
        for name, value in constants:
            r += "constant,{},{},,\n".format(name.lower(), value)

    if memory_regions is not None:
        for name, origin, length in memory_regions:
            r += "memory_region,{},0x{:08x},{:d},\n".format(name.lower(), origin, length)

    return r
