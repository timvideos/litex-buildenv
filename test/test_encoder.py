import socket

sock  = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("", 8000))

f = open("test.bin", "wb")
while True:
    data, addr = sock.recvfrom(8192)
    f.write(data)
f.close()
