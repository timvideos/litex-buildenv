

from myhdl import *

def HeaderRam(d, waddr, raddr, we, clk, q):
    
    fp = open('header.hex', 'r')
    ba = []
    for line in fp:
        bv = int(line.strip(), 16)
        ba.append(bv)
    ba = tuple(ba)
    msz = max(len(waddr), len(raddr))    
    mem = [Signal(intbv(0)[8:]) for _ in range(2**msz)]

    read_addr = Signal(raddr)
    use_ram = Signal(bool(0))

    @always(clk.posedge)
    def rtl():
        if we:
            use_ram.next = True
            mem[waddr].next = d
        read_addr.next = raddr
        
    @always_comb
    def rtl_out():
        if use_ram:
            q.next = mem[read_addr]
        else:
            q.next = ba[read_addr]

    return rtl, rtl_out
            

def convert():
    d = Signal(intbv(0)[8:])
    q = Signal(intbv(0)[8:])
    raddr = Signal(intbv(0)[10:])
    waddr = Signal(intbv(0)[10:])
    clk = Signal(bool(0))
    we = Signal(bool(0))
    HeaderRam(d, waddr, raddr, we, clk, q)
    toVHDL.numeric_ports = False
    toVHDL(HeaderRam, d, waddr, raddr, we, clk, q)

if __name__ == '__main__':
    convert()