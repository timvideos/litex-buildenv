import platform
import ctypes
import re
import os
import sys
import time
import queue
import threading
import collections

_lpath = (os.path.dirname(__file__))
if _lpath == '':
	_lpath = '.'
if platform.system() == "Windows":
	libftdicom =  ctypes.cdll.LoadLibrary(_lpath + "/libftdicom.dll")
else:
	libftdicom =  ctypes.cdll.LoadLibrary(_lpath + "/libftdicom.so")

class FTDI_Device(ctypes.Structure):
	_fields_ = [
		('_1', ctypes.c_void_p),
		('_2', ctypes.c_void_p),
	]

pFTDI_Device = ctypes.POINTER(FTDI_Device)

# FTDIDevice_Open
FTDIDevice_Open = libftdicom.FTDIDevice_Open
FTDIDevice_Open.argtypes = [pFTDI_Device]
FTDIDevice_Open.restype = ctypes.c_int

# FTDIDevice_Close
FTDIDevice_Close = libftdicom.FTDIDevice_Close
FTDIDevice_Close.argtypes = [pFTDI_Device]

FTDIDevice_SetMode = libftdicom.FTDIDevice_SetMode
FTDIDevice_SetMode.argtypes = [
		pFTDI_Device, # Dev
		ctypes.c_int, # Interface
		ctypes.c_int, # Mode
		ctypes.c_char, # PinDirection
		ctypes.c_char, # baudrate
	]


FTDIDevice_Write = libftdicom.FTDIDevice_Write
FTDIDevice_Write.argtypes = [
		pFTDI_Device, # Dev
		ctypes.c_int, # Interface
		ctypes.c_char_p, # Buf
		ctypes.c_size_t, # N
		ctypes.c_bool, # async
	]
FTDIDevice_Write.restype = ctypes.c_int

p_cb_StreamCallback = ctypes.CFUNCTYPE(
		ctypes.c_int,    # retval
		ctypes.POINTER(ctypes.c_uint8), # buf
		ctypes.c_int, # length
		ctypes.c_void_p, # progress
		ctypes.c_void_p) # userdata

FTDIDevice_ReadStream = libftdicom.FTDIDevice_ReadStream
FTDIDevice_ReadStream.argtypes = [
		pFTDI_Device,    # dev
		ctypes.c_int,    # interface
		p_cb_StreamCallback, # callback
		ctypes.c_void_p, # userdata
		ctypes.c_int, # packetsPerTransfer
		ctypes.c_int, # numTransfers
		]
FTDIDevice_ReadStream.restype = ctypes.c_int

FTDI_INTERFACE_A = 1
FTDI_INTERFACE_B = 2

FTDI_BITMODE_SYNC_FIFO = (1 << 6)

class FTDIDevice:
	def __init__(self):
		self.__is_open = False
		self._dev = FTDI_Device()

	def __del__(self):
		if self.__is_open:
			self.__is_open = False
			FTDIDevice_Close(self._dev)

	def open(self):
		err = FTDIDevice_Open(self._dev)
		if err:
			return err
		else:
			self.__is_open = True

		return err

	def write(self, intf, buf, async=False):
		if not isinstance(buf, bytes):
			raise TypeError("buf must be bytes")

		return FTDIDevice_Write(self._dev, intf, buf, len(buf), async)

	def read(self, intf, n):
		buf = []

		def callback(b, prog):
			buf.extend(b)
			return int(len(buf) >= n)

		self.read_async(intf, callback, 4, 4)

		return buf

	def read_async(self, intf, callback, packetsPerTransfer, numTransfers):
		def callback_wrapper(buf, ll, prog, user):
			if ll:
				b = ctypes.string_at(buf, ll)
			else:
				b = b''
			return callback(b, prog)

		cb = p_cb_StreamCallback(callback_wrapper)

		return FTDIDevice_ReadStream(self._dev, intf, cb,
				None, packetsPerTransfer, numTransfers)

class ProtocolError(Exception):
	pass

class TimeoutError(Exception):
	pass

INCOMPLETE = -1
UNMATCHED = 0
class BaseService:
	def match_identifier(self, byt):
		r = True
		r = r and (byt[0] == 0x5A)
		r = r and (byt[1] == 0xA5)
		r = r and (byt[2] == 0x5A)
		r = r and (byt[3] == 0xA5)
		r = r and (byt[4] == self.tag)
		return r

	def get_needed_size_for_identifier(self):
		return self.NEEDED_FOR_SIZE

	def present_bytes(self, b):
		if len(b) < self.get_needed_size_for_identifier():
			return INCOMPLETE

		if not self.match_identifier(b):
			return UNMATCHED

		size = self.get_packet_size(b)

		if len(b) < size:
			return INCOMPLETE

		self.consume(b[:size])

		return size

class UART:
	class __UARTService(BaseService):
		NEEDED_FOR_SIZE = 9

		def __init__(self, tag):
			self.tag = tag
			self.q = queue.Queue()

		def get_packet_size(self, buf):
			return 10

		def consume(self, buf):
			self.q.put(buf[9])

	def __init__(self, tag):
		self.tag = tag
		self.service = UART.__UARTService(self.tag)

	def do_read(self, timeout=None):
		try:
			resp = self.service.q.get(True, timeout)
		except queue.Empty:
			return -1
		return resp

	def do_write(self, value):
		msg = [0x5A, 0xA5, 0x5A, 0xA5, self.tag, 0x00, 0x00, 0x00, 1, value&0xFF]
		self.service.write(bytes(msg))

class DMA:
	class __DMAService(BaseService):
		NEEDED_FOR_SIZE = 9

		def __init__(self, tag):
			self.tag = tag
			self.q = queue.Queue()

		def get_packet_size(self, buf):
			payload_size = buf[5] << 24
			payload_size |= buf[6] << 16
			payload_size |= buf[7] << 8
			payload_size |= buf[8] << 0
			return 9 + payload_size

		def consume(self, buf):
			self.q.put(buf[9:])

	def __init__(self, tag):
		self.tag = tag
		self.service = DMA.__DMAService(self.tag)

	def do_read(self, timeout=None):
		try:
			resp = list(self.service.q.get(True, timeout))
		except queue.Empty:
			raise TimeoutError("DMA read timed out")
		return resp

	def do_write(self, data):
		length = len(data)
		msg = [0x5A, 0xA5, 0x5A, 0xA5, self.tag,
			(length & 0xff000000) >> 24,
			(length & 0x00ff0000) >> 16,
			(length & 0x0000ff00) >> 8,
			(length & 0x000000ff) >> 0]
		msg += data
		self.service.write(bytes(msg))

class FTDIComDevice:
	def __init__(self, uart_tag=0, dma_tag=1, verbose=False):
		self.__is_open = False

		self.dev = FTDIDevice()
		self.verbose = verbose

		self.uart = UART(uart_tag)
		self.dma = DMA(dma_tag)

		self.__services = [self.uart.service, self.dma.service]

		# Inject a write function into the services
		for service in self.__services:
			def write(msg):
				if self.verbose:
					print("< %s" % " ".join("%02x" % i for i in msg))

				self.dev.write(FTDI_INTERFACE_B, msg, async=False)

			service.write = write

	def __comms(self):
		self.__buf = b""

		def callback(b, prog):
			try:
				if self.verbose and b:
					print("> %s" % " ".join("%02x" % i for i in b))

				self.__buf += b

				incomplete = False

				while self.__buf and not incomplete:
					for service in self.__services:
						code = service.present_bytes(self.__buf)
						if code == INCOMPLETE:
							incomplete = True
							break
						elif code:
							self.__buf = self.__buf[code:]
							break
					else:
						self.__buf = self.__buf[1:]

				return int(self.__comm_term)
			except Exception as e:
				self.__comm_term = True
				self.__comm_exc = e
				return 1

		while not self.__comm_term:
			self.dev.read_async(FTDI_INTERFACE_B, callback, 8, 16)

		if self.__comm_exc:
			raise self.__comm_exc

	def __del__(self):
		if self.__is_open:
			self.close()

	def open(self):
		if self.__is_open:
			raise ValueError("FTDICOMDevice doubly opened")

		stat = self.dev.open()
		if stat:
			print("USB: Error opening device\n")
			return stat

		self.commthread = threading.Thread(target=self.__comms, daemon=True)
		self.__comm_term = False
		self.__comm_exc = None

		self.commthread.start()

		self.__comm_term = False
		self.__is_open = True

	def close(self):
		if not self.__is_open:
			raise ValueError("FTDICOMDevice doubly closed")

		self.__comm_term = True
		self.commthread.join()

		self.__is_open = False

	def uartflush(self, timeout=0.25):
		while (self.uartread(timeout) != -1):
			pass

	def uartread(self, timeout=None):
		return self.uart.do_read(timeout)

	def uartwrite(self, value):
		return self.uart.do_write(value)

	def dmaread(self):
		return self.dma.do_read()

	def dmawrite(self, data):
		return self.dma.do_write(data)

def uart_console(ftdi_com):
	def read():
		while True:
			print(chr(ftdi_com.uartread()), end="")

	readthread = threading.Thread(target=read, daemon=True)
	readthread.start()

	def write():
		while True:
			for e in input():
				c = ord(e)
				ftdi_com.uartwrite(c)
			ftdi_com.uartwrite(ord("\n"))


	writethread = threading.Thread(target=write, daemon=True)
	writethread.start()

def uart_virtual(ftdi_com):
	import pty, serial
	master, slave = pty.openpty()
	s_name = os.ttyname(slave)
	ser = serial.Serial(s_name)

	def read():
		while True:
			s = ftdi_com.uartread()
			s = bytes(chr(s).encode('utf-8'))
			os.write(master, s)

	readthread = threading.Thread(target=read, daemon=True)
	readthread.start()

	def write():
		while True:
			for c in list(os.read(master, 100)):
				ftdi_com.uartwrite(c)

	writethread = threading.Thread(target=write, daemon=True)
	writethread.start()

	return s_name

if __name__ == "__main__":
	ftdi_map = {
		"uart": 0,
		"dma":  1
	}
	ftdi_com = FTDIComDevice(ftdi_map["uart"], ftdi_map["dma"], verbose=False)
	ftdi_com.open()
	# test DMA
	for i in range(256):
		ftdi_com.dmawrite([i])
		print("%02x" %(ftdi_com.dmaread()[0]), end="")
		sys.stdout.flush()
	print("")
	# test UART
	if platform.system() == "Windows":
		uart_console(ftdi_com) # redirect uart to console since pty does not exist on Windows platforms
	else:
		s_name = uart_virtual(ftdi_com)
		print(s_name)
	while True:
		time.sleep(1)
