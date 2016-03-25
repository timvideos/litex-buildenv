#!/usr/bin/python3

import sys
import re
import os

if "--verbose" not in sys.argv:
	verbose = False
	def write(*args, **kw):
		pass
else:
	verbose = True
	write = sys.stderr.write

prefix = sys.argv[-1]
prefix_re = '"(%s[^"]*)"' % prefix.replace('/', '/+')

cmds = {}
finished_cmds = {}
waiting_on = {}
files = set()

last_pid = None
for lineno, rawline in enumerate(sys.stdin.readlines()):
	try:
		bits = re.match(r"^(?P<pid>[0-9]+) (?P<line>.*?)(?P<unfinished> <unfinished \.\.\.>)?$", rawline)

		pid = bits.group('pid')
		line = bits.group('line')

		if pid != last_pid:
			if pid not in cmds:
				if "execve" in line:
					write("%08i: fork+exec, using new line %r\n" % (lineno, line))
					cmds[pid] = line
				else:
					if last_pid in cmds:
						last_command = cmds[last_pid] 
					else:
						last_command = finished_cmds[last_pid]
					write("%08i: Not a fork+exec (%r), using last line %r\n" % (lineno, line, last_command))
					cmds[pid] = last_command
		last_pid = pid

		# Connect together lines where the kernel switched between processes
		# 31093 vfork( <unfinished ...>
		# 31439 execve("/opt/Xilinx/14.7/ISE_DS/ISE/bin/lin64/unwrapped/wbtc", ["/opt/Xilinx/14.7/ISE_DS/ISE/bin/"..., "-f", "/home/tansell/foss/timvideos/hdm"...], [/* 79 vars */]) = 0
		# 31093 <... vfork resumed> )   
		unfinished = bits.group('unfinished')
		assert "<unfinished ...>" not in line
		if unfinished:
			assert pid not in waiting_on
			waiting_on[pid] = line + unfinished
			continue
		if "resumed>" in line:
			assert pid in waiting_on
			line = waiting_on[pid] + " " + line
			del waiting_on[pid]

		if "exited with" in line:
			assert pid not in waiting_on
			finished_cmds[pid] = cmds[pid]
			del cmds[pid]
			continue
		else:
			assert pid in cmds

		# Command exec tracking
		if "execve" in line and cmds[pid] != line:
			write("%08i: Replacing %r with %r\n" % (lineno, cmds[pid], line))
			cmds[pid] = line

		# Did the syscall succeed?
		success = "-1 ENOENT" not in line

		# Does the syscall use the prefix?
		bits = re.search(prefix_re, line)
		if not bits:
			continue

		# Normalize the path
		path = bits.group(1)
		path = os.path.normpath(path)
		if path.startswith('//'):
			path = path[1:]

		assert path.startswith(prefix)
		
		# Did the file exist?
		if not success:
			assert not os.path.exists(path)
			continue
		else:
			assert os.path.exists(path)

		# Skip directories
		if os.path.isdir(path):
			continue

		write("%08i: Found %r via command %r (Previously seen: %r)\n" % (lineno, path, cmds[pid], path in files))

		files.add(path)
	except Exception as e:
		sys.stderr.write("%08i: %r %r\n" % (lineno, e, rawline))
		raise

for filename in sorted(files):
	print(filename)
