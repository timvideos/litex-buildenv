#!/usr/bin/env python3

import struct
import socket
import argparse
import time

parser = argparse.ArgumentParser()

parser.add_argument("-i", "--input")
parser.add_argument("-a", "--addr", default='10.0.0.50')
parser.add_argument("-p", "--port", default='6000')

args = parser.parse_args()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

s.connect((args.addr, int(args.port)))

with open(args.input, 'rb') as f:
    dat = f.read()

def reverse(buf):
    size = int(len(buf)/4)

    return struct.pack('<{}I'.format(size), *struct.unpack('>{}I'.format(size), buf))

pkt = struct.pack("{}B".format(len(dat)), *dat)

start = time.time()
s.send(reverse(pkt))
end = time.time()

print('xfer speed {} KB/s'.format((len(pkt) / 1024)/(end - start)))
