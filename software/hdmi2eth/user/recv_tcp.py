#!/usr/bin/env python3

import struct
import socket
import argparse
import time

def reverse(buf):
    size = int(len(buf)/4)

    return struct.pack('<{}I'.format(size), *struct.unpack('>{}I'.format(size), buf))

parser = argparse.ArgumentParser()

parser.add_argument("-o", "--output", default='capture.UYVY')
parser.add_argument("-a", "--addr", default='10.0.0.50')
parser.add_argument("-p", "--port", default='6001')

args = parser.parse_args()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

s.connect((args.addr, int(args.port)))

start = time.time()

size = s.recv(4)

size = struct.unpack('I', size)[0]

print(size)

i = 0
data = bytearray()

while i < size:
    xfer_size = min(4096, size - i)
    chunk = bytearray(s.recv(xfer_size))
    data.extend(chunk)
    i = i + len(chunk)

end = time.time()

with open(args.output, 'wb') as f:
    f.write(reverse(data))

print('xfer speed {} KB/s'.format((size / 1024)/(end - start)))
