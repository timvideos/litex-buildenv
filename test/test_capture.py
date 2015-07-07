import os
import subprocess
import socket

capture_dir = "./captures/"
capture_filename = "capture.bin"
jpg_filename = "capture_{}.jpg"
capture_size = 10*1024*1024

sock  = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("", 8000))

# clean capture_dir
subprocess.call(["rm", "-rf", capture_dir + "/*"])

# capture data
data_size = 0
f = open(os.path.join(capture_dir, capture_filename), "wb")
while data_size <= capture_size:
    data, addr = sock.recvfrom(8192)
    data_size += len(data)
    f.write(data)
f.close()

# split data in jpg files
def split_capture(f):
    c = bytearray()
    while True:
        b = f.read(1048)
        if not b: # end-of-file
            yield data
            return
        c += b
        while True:
            pos = c.find(bytearray(b"\xff\xd9"))
            if pos < 0:
                break
            yield c[:pos]
            c = c[pos + 2:]

for i, capture in enumerate(split_capture(open(os.path.join(capture_dir, capture_filename), 'rb'))):
    f = open(os.path.join(capture_dir, jpg_filename.format(str(i))), "wb")
    f.write(capture)
    f.close()
