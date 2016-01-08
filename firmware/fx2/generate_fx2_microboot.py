#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: set ts=4 sw=4 et sts=4 ai:

from __future__ import print_function

import binascii
import ctypes
import time
import re

class DynamicLengthStructure(ctypes.LittleEndianStructure):
    r"""
    """
    _pack_ = 1

    @property
    def len(self):
        return self._len

    @len.setter
    def len(self, value):
        rsize = value
        if ctypes.sizeof(self) < rsize:
            try:
                ctypes.resize(self, rsize)
            except ValueError:
                raise ValueError("Need %s more space" % (rsize - ctypes.sizeof(self)))

        self._len = value

    @property
    def data(self):
        addr = ctypes.addressof(self)
        return (ctypes.c_ubyte * self.len).from_address(addr+self._extra_end)

    def as_bytearray(self):
        return bytearray((ctypes.c_ubyte * ctypes.sizeof(self)).from_address(ctypes.addressof(self)))


class _ConfigCommon(ctypes.LittleEndianStructure):

    def segments(self):
        segs = []
        segment = self.next()
        while segment is not None:
            segs.append(segment)
            segment = segment.next()
        return segs

    @property
    def totalsize(self):
        l = ctypes.sizeof(self.__class__)
        for seg in self.segments():
            l += ctypes.sizeof(seg.__class__)
            l += seg._len
        return l


class _DataSegment(ctypes.BigEndianStructure):

    @property
    def data(self):
        addr = ctypes.addressof(self)
        return (ctypes.c_ubyte * self._len).from_address(addr+self.__class__._data.offset)

    @property
    def len_bits(self):
        return int(re.search("bits=([0-9]+)", repr(self.__class__._len)).groups()[0])+1

    def next(self):
        if self.last:
            return None
        addr = ctypes.addressof(self)
        addr += ctypes.sizeof(self)
        addr += self._len
        return self.__class__.from_address(addr)

    def check(self):
        if self.last:
            assert self._last == 1
            assert self._len == 0
            assert self.addr == 0
        else:
            assert 0 <= self.addr <= 0x3FFF or 0xE00 <= self.addr <= 0xE1FF, self.addr

    def __repr__(self):
        return "%s(0x%04x, {...}[%i])" % (self.__class__.__name__, self.addr, self._len)

    @property
    def last(self):
        return bool(self._last)

    def make_last(self):
        self._last = 1

    def clear(self):
        self._last = 0
        self.addr = 0
        self._len = 0
        assert len(self.data) == 0, len(self.data)

    def c_struct(self, name):
        return """\
        struct {
            __be%i  len;
            __be16  addr;
            __u8    data[%i];
        } __attribute__ ((packed)) %s""" % (
            self.len_bits, self._len, name)

    def c_fill(self):

        s = []
        s.append("""{
        .len        = htobe%ic(0x%02X)%s,
        .addr       = htobe16c(0x%04X),
        .data       = {
            """ % (self.len_bits, self._len, ['',  ' | (1 << %s)' % (self.len_bits-1)][self.last], self.addr))
        for j, b in enumerate(self.data):
            s.append("0x%02X, " % b)
            if (j+1) % 8 == 0:
                s.append("""
            """)
        s.append("""
        }
    }""")
        return "".join(s)



class MicrobootSegment(_DataSegment):
    _pack_ = 1
    _fields_ = [
        ("_last", ctypes.c_uint8, 1),
        ("_len", ctypes.c_uint8, 7),
        ("addr", ctypes.c_uint16),
        ("_data", ctypes.c_ubyte * 0),
    ]

    MAX_LEN = 2**7-1

    def make_last(self):
        self._last = 1
        self._len = 0
        self.addr = 0
        self._data[:] = []


class MicrobootConfig(_ConfigCommon):
    _pack_ = 1
    _fields_ = []

    def next(self):
        return MicrobootSegment.from_address(ctypes.addressof(self))

    def c_struct(self, name):
        uname = name.upper()
        segs = self.segments()
        s = []
        s.append("""\
#define %s_END offsetof(union %s_t, data%i)+1
""" % (uname, name, len(segs)-1))
        s.append("""\
union %s_t {
    struct {
""" % name)
        for i, seg in enumerate(segs):
            s.append(seg.c_struct("data%i" % i))
            s.append(";\n")
        s.append("""\
    };
    __u8 bytes[%i];
} %s""" % (self.totalsize, name))
        return "".join(s)

    def c_fill(self):
        s = []
        segs = self.segments()
        s.append("""{
""")
        for i, seg in enumerate(segs):
            s.append("""\
    .data%s = """ % i)
            s.append(seg.c_fill())
            s.append(",\n")
        s.append("""\
};
""")
        return "".join(s)

    def c_code(self, name="fx2fw"):
        return "".join([
            self.c_struct(name),
            " = ",
            self.c_fill(),
        ])


def microboot_from_hexfile(filename):
    import hexfile
    hexf = hexfile.load(filename)

    # Work out the number of bytes needed
    totalsize = ctypes.sizeof(MicrobootConfig)
    for i, segment in enumerate(hexf.segments):
        start = 0
        while True:
            totalsize += ctypes.sizeof(MicrobootSegment)
            partsize = min(MicrobootSegment.MAX_LEN, segment.size - start)
            start += partsize
            if start >= segment.size:
                break
        totalsize += segment.size
    totalsize += ctypes.sizeof(MicrobootSegment)

    backbuffer = bytearray(totalsize+100)

    # FX2 header
    mb2cfg = MicrobootConfig.from_buffer(backbuffer)
    mb2cfg.buffer = backbuffer

    # FX2 data segments
    mb2seg = mb2cfg
    for i, segment in enumerate(hexf.segments):
        start = 0
        while True:
            mb2seg = mb2seg.next()
            partsize = min(mb2seg.MAX_LEN, segment.size - start)
            mb2seg.addr = segment.start_address + start
            mb2seg._len = partsize
            mb2seg.data[:] = segment.data[start:start+partsize]
            start += partsize
            if start >= segment.size:
                break

    mb2seg = mb2seg.next()
    mb2seg.make_last()
    assert totalsize == mb2cfg.totalsize

    return mb2cfg


if __name__ == "__main__":
    import os
    import sys
    name = ""
    mb2cfg = microboot_from_hexfile(sys.argv[1])
    name = "_"+(os.path.splitext(os.path.basename(sys.argv[1]))[0]).lower()

    sys.stderr.write("%s segments in FX2 firmware\n" % len(mb2cfg.segments()))
    sys.stdout.write("""\
#include <endian.h>
#include <stdint.h>

#ifndef __bswap_constant_16
#define __bswap_constant_16(x) \
    ((unsigned short int) ((((x) >> 8) & 0xff) | (((x) & 0xff) << 8)))
#endif

// Constant versions of the htobe functions for use in the structures
#if __BYTE_ORDER == __LITTLE_ENDIAN
# define htobe16c(x) __bswap_constant_16(x)
# define htole16c(x) (x)
#else
# define htobe16c(x) (x)
# define htole16c(x) __bswap_constant_16(x)
#endif

typedef uint8_t __u8;
typedef uint16_t __le16;
typedef uint16_t __be16;

typedef __u8 __le8;
typedef __u8 __be8;
#define htobe8c(x) (x)
#define htole8c(x) (x)
""")
    sys.stdout.write(mb2cfg.c_code("fx2_mbfw" + name))
