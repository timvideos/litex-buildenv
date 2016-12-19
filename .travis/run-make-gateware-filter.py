#!/usr/bin/python

import collections
import os
import pprint
import re
import signal
import subprocess
import sys
import threading
import time

log_file = open(sys.argv[1], 'w+')

# Suppressions for warning / info messages
#suppressions = [x.strip() for x in open(sys.argv[2], 'r').readlines() if not x.startswith('#')]
#suppressions = [re.compile(x) for x in suppressions]

top_path = os.path.normpath(os.getcwd())

def output(s, *args, **kw):
	with keepalive_thread.lock:
		if "before_next_output" in kw:
			before_next_output = kw["before_next_output"]
			del kw["before_next_output"]
		else:
			before_next_output = ""

		keepalive_thread.output = True
		if args:
			assert not kw
			data = (s % args).encode('utf-8')
		elif kw:
			data = (s % kw).encode('utf-8')
		else:
			data = s.encode('utf-8')

		if data:
			sys.stdout.write(keepalive_thread.before_next_output)
			keepalive_thread.before_next_output = before_next_output
			sys.stdout.flush()

			sys.stdout.write(data)
			keepalive_thread.last_output_time = time.time()
			keepalive_thread.last_output = data
			sys.stdout.flush()


class KeepAliveThread(threading.Thread):
	ROTATE = [" - ", " \\ ", " | ", " / "]

	def __init__(self):
		threading.Thread.__init__(self)
		self.lock = threading.RLock()
		self.daemon = True

		self.pos = 0
		self.output = False
		self.before_next_output = ""
		self.last_output_time = time.time()
		self.last_output = ""

	def run(self):
		while True:
			if (time.time() - self.last_output_time) > 1:
				output(self.ROTATE[self.pos], before_next_output="\b\b\b")
				self.pos = (self.pos + 1) % len(self.ROTATE)
			time.sleep(1)

keepalive_thread = KeepAliveThread()
keepalive_thread.start()

BUFFER_SIZE=200
DELIM_MAJOR = "========================================================================="
ERROR = "*~"*35+"*"

linesbuffer = collections.deque()
for i in range(0, BUFFER_SIZE):
	linesbuffer.appendleft('')

def shorten_path(line):
	outputline = line
	for path in re.finditer('"([^"]+)"', line):
		pathname = os.path.normpath(path.group(1))
		if os.path.exists(pathname) and os.path.isfile(pathname):
			common_path = os.path.commonprefix([top_path, pathname])
			relative_path = pathname[len(common_path)+1:]

			outputline = outputline.replace(path.group(1), relative_path)
	return outputline


fsm_triggered = False
found_specials = []

last_path = None
for lineno, rawline in enumerate(sys.stdin.xreadlines()):
	log_file.write(rawline)
	log_file.flush()

	line = rawline.strip('\n\r')
	sline = line.strip()
	linesbuffer.appendleft(line)
	while len(linesbuffer) > BUFFER_SIZE:
		linesbuffer.pop()

	if line.startswith("make"):
		output('\n%s ', line)
		continue

	if not sline:
		continue

	if line.startswith("ERROR:"):
		linesbuffer.popleft()
		output("\n\nError detected! - %s\n%s\n%s\n%s\n%s", line, ERROR, "\n".join(reversed(linesbuffer)), ERROR, rawline)
		break

	# WARNING:HDLCompiler:1016 - "/home/tansell/foss/timvideos/hdmi2usb/HDMI2USB-misoc-firmware/build/misoc/build/atlys_hdmi2usb-hdmi2usbsoc-atlys.v" Line 24382: Port I_LOCK_O is not connected to this instance
	# WARNING:HDLCompiler:1016 - "/home/tansell/foss/timvideos/hdmi2usb/HDMI2USB-misoc-firmware/build/misoc/build/atlys_hdmi2usb-hdmi2usbsoc-atlys.v" Line 24475: Port IOCLK is not connected to this instance
	# WARNING:Xst:3035 - Index value(s) does not match array range for signal <storage_20>, simulation mismatch.
	# INFO:Xst:2774 - HDL ADVISOR - KEEP property attached to signal eth_rx_clk may hinder XST clustering optimizations.
	keepalive_thread.output = False
	if line.startswith("WARNING:"):
		output("w")
		continue
	elif line.startswith("INFO:"):
		output("i")
		continue

	# Different tools start with the following
	# Release 14.7 - Map P.20131013 (lin64)
	# Copyright (c) 1995-2013 Xilinx, Inc.  All rights reserved.
	if sline.startswith("Copyright (c)"):
		output("\n\n\n%s\n# %-66s #\n%s\n", "#"*70, linesbuffer[1], "#"*70)
		continue

	######################################################################
	# Release 14.7 - xst P.20131013 (lin64)                              #
	######################################################################
		
	# Output a header which looks like this unless it is a summary header
	# =========================================================================
	# *                          HDL Parsing                                  *
	# =========================================================================
	if linesbuffer[0] == DELIM_MAJOR and \
	   linesbuffer[1].startswith("*") and \
	   linesbuffer[2] == DELIM_MAJOR:
		if "Summary" in linesbuffer[1]:
			continue
		else:
			output("\n\n%s\n* %-66s *\n%s\n", '*'*70, linesbuffer[1][2:-2].strip(), '*'*70)
			continue

	# When we see a filename, output it. Examples;
	# Analyzing Verilog file "/home/tansell/foss/timvideos/hdmi2usb/HDMI2USB-misoc-firmware/build/misoc/extcores/lm32/submodule/rtl/lm32_dp_ram.v" into library work
	# Parsing verilog file "/home/tansell/foss/timvideos/hdmi2usb/HDMI2USB-misoc-firmware/build/misoc/extcores/lm32/submodule/rtl/lm32_include.v" included at line 31.
	# Parsing module <lm32_dp_ram>.
	# Analyzing Verilog file "/home/tansell/foss/timvideos/hdmi2usb/HDMI2USB-misoc-firmware/build/misoc/extcores/lm32/submodule/rtl/lm32_shifter.v" into library work
	# Parsing verilog file "/home/tansell/foss/timvideos/hdmi2usb/HDMI2USB-misoc-firmware/build/misoc/extcores/lm32/submodule/rtl/lm32_include.v" included at line 50.
	# Parsing module <lm32_shifter>.
	#for path in re.finditer('"([^"]+)"', line):
	#	pathname = os.path.normpath(path.group(1))
	#	if os.path.exists(pathname) and os.path.isfile(pathname):
	#		if pathname != last_path:
	#			last_path = pathname
	#			
	#			common_path = os.path.commonprefix([top_path, pathname])
	#			relative_path = pathname[len(common_path)+1:]
	#
	#			output("\n  %s ", relative_path)

	#########################################################################
	# Synthesis Options Summary && 8) Design Summary
	###########################################################################
	# =========================================================================
	# *                      Synthesis Options Summary                        *
	# =========================================================================
	# ---- Source Parameters
	# Input File Name                    : "atlys_hdmi2usb-hdmi2usbsoc-atlys.prj"
	# ...
	# ...
	# =========================================================================
	###########################################################################
	# =========================================================================
	# *                            Design Summary                             *
	# =========================================================================
	# ...
	#
	# =========================================================================
	if line == DELIM_MAJOR:
		summary_start = None
		for bufferno, bufline in enumerate(linesbuffer):
			if bufferno == 0 or bufferno+1 == len(linesbuffer):
				continue
			sbufline = bufline.strip()
			if sbufline != DELIM_MAJOR:
				continue

			summaryline = linesbuffer[bufferno+1].strip()
			if not summaryline.startswith("*") or "Summary" not in summaryline:
				break
			summary_start = bufferno+2
			break

		if summary_start:
			output("\n\n")
			for i in range(summary_start, 0, -1):
				sbufline = linesbuffer[i].strip()
				if sbufline == DELIM_MAJOR:
					output("%s\n", "*"*70)
				elif sbufline.startswith('*'):
					output("* %-66s *\n", sbufline[2:-2].strip())
				else:
					if linesbuffer[i].startswith('#'):
						output("%s\n", linesbuffer[i][1:])
					else:
						output("%s\n", linesbuffer[i])

	#########################################################################
	# 2) HDL Parsing
	# -----------------------------------------------------------------------
	# Analyzing Verilog file "/home/tansell/foss/timvideos/hdmi2usb/HDMI2USB-misoc-firmware/build/misoc/extcores/lm32/submodule/rtl/lm32_dtlb.v" into library work
	ANALYZING_VERILOG = "Analyzing Verilog"
	if sline.startswith(ANALYZING_VERILOG):
		output("\n%s ", shorten_path(sline))
	
	# Parsing package <MDCT_PKG>.
	# Parsing module <lm32_addsub>.
	# Parsing entity <ByteStuffer>.
	# Parsing architecture <RTL> of entity <bytestuffer>.
	PARSING = "Parsing "
	if sline.startswith(PARSING):
		if sline.startswith("Parsing VHDL"):
			output("\n%s ", shorten_path(sline))
		else:
			if sline.endswith('.'):
				sline = sline[:-1]
			output("\n  %s ", shorten_path(sline))
		#bits = re.match(PARSING+"([^ ]+) .*<([^>]+)>\\.", sline)
		#if bits:
		#	output("\nParsing %s %s ", bits.group(1), bits.group(2))


	#########################################################################
	# 3) HDL Elaboration
	# -----------------------------------------------------------------------
	# Elaborating module <$unit_1>.
	ELABORATION = "Elaborating "
	if sline.startswith(ELABORATION):
		if sline.endswith('.'):
			sline = sline[:-1]
		output("\n%s ", sline)
		#bits = re.match(ELABORATION+"([^ ]+) .*?<([^>]+)>(.+from library <[^>]+>)?\\.", sline)
		#if bits:
		#	output("\nElaborating %s %s ", bits.group(1), bits.group(2))

	# Reading initialization file
	READING_INIT = "Reading initialization file"
	if sline.startswith(READING_INIT):
		if sline.endswith('.'):
			sline = sline[:-1]
		output("\n  %s ", sline.replace('\\"', '"'))

	#########################################################################
	# 4) HDL Synthesis
	# -----------------------------------------------------------------------

	# Synthesizing Unit <top>.
	#    Related source file is "/home/tansell/foss/timvideos/hdmi2usb/HDMI2USB-misoc-firmware/build/misoc/build/atlys_hdmi2usb-hdmi2usbsoc-atlys.v".
	#    Set property "register_balancing = no" for signal <ethmac_tx_cdc_graycounter0_q>.
	#    Set property "register_balancing = no" for signal <ethmac_tx_cdc_graycounter1_q>.
	#    Set property "register_balancing = no" for signal <ethmac_rx_cdc_graycounter0_q>.
	SYNTH = "Synthesizing Unit"
	if sline.startswith(SYNTH):
		if sline.endswith('.'):
			sline = sline[:-1]
		output("\n%s ", sline)

	RELATED_SOURCE = "Related source file is"
	if sline.startswith(RELATED_SOURCE):
		if sline.endswith('.'):
			sline = sline[:-1]
		output("\n  %s ", shorten_path(sline))

	# Collect special blocks for output in summary.
	#    Found 128x24-bit dual-port RAM <Mram_mem> for signal <mem>.
	SPECIALS = ["RAM"]
	if sline.startswith("Found"):
		special_found = False
		for special in SPECIALS:
			if special in sline:
				special_found = True
				break
		if special_found:
			found_specials.append(sline)

	#    Summary:
	#	inferred  64 RAM(s).
	#	inferred  16 Multiplier(s).
	#	inferred 409 Adder/Subtractor(s).
	#	inferred 8597 D-type flip-flop(s).
	#	inferred 140 Comparator(s).
	#	inferred 1536 Multiplexer(s).
	#	inferred   6 Combinational logic shifter(s).
	#	inferred   2 Tristate(s).
	#	inferred  32 Finite State Machine(s).
	# Unit <top> synthesized.
	SUMMARY = "Summary:"
	SYTH = "synthesized."
	if sline.endswith(SYTH):
		summary_start = None
		for bufferno, bufline in enumerate(linesbuffer):
			sbufline = bufline.strip()
			if sbufline.endswith(SUMMARY):
				summary_start = bufferno
				break
		if summary_start:
			output("\n  Summary:\n")
			for special in sorted(found_specials):
				output("    %s\n", special)
			if found_specials:
				output("    %s\n", "--")
			found_specials = []
			for bufferno in range(summary_start-1, 0, -1):
				sbufline = linesbuffer[bufferno].strip()
				output("    %s\n", sbufline[0].upper()+sbufline[1:-1])

	#########################################################################
	# 5) Advanced HDL Synthesis
	# -----------------------------------------------------------------------
	SYNTH_ADV = "Synthesizing (advanced) Unit"
	if sline.startswith(SYNTH_ADV):
		if sline.endswith('.'):
			sline = sline[:-1]
		output("\n%s ", sline)

	#########################################################################
	# 6) Low Level Synthesis
	# -----------------------------------------------------------------------

	# Analyzing FSM <MFsm> for best encoding.
	# Optimizing FSM <FSM_0> on signal <clockdomainsrenamer3_state[1:2]> with user encoding.
	if sline.startswith("Analyzing FSM") or sline.startswith("Optimizing FSM"):
		if not fsm_triggered:
			output("\nAnalyzing and optimizing FSMs ")
			fsm_triggered = True
		else:
			output(".")
		continue

	# Optimizing unit <JpegEnc> ...
	# Optimizing unit <RAMZ_1> ...
	OPTIMIZING = "Optimizing unit"
	if sline.startswith(OPTIMIZING):
		if sline.endswith('.'):
			sline = sline[:-1]
		output("\n%s ", sline)

	# Processing Unit <top> :
	PROCESSING = "Processing Unit "
	if sline.startswith(PROCESSING):
		if sline.endswith(' :'):
			sline = sline[:-2]
		output("\n%s ", sline)

	# Final Macro Processing ...
	if sline == "Final Macro Processing ...":
		output("\n%s" % sline)
	

	#########################################################################
	# 7) Partition Report
	# -----------------------------------------------------------------------
	
	# Nothing?

	#########################################################################
	# 8) Design Summary
	# -----------------------------------------------------------------------

	######################################################################
	# Release 14.7 - ngdbuild P.20131013 (lin64)                         #
	######################################################################

	######################################################################
	# Release 14.7 - Map P.20131013 (lin64)                              #
	######################################################################

	if sline.startswith("Peak Memory Usage"):
		summary_start = None
		for bufferno, bufline in enumerate(linesbuffer):
			sbufline = bufline.strip()
			if sbufline.startswith("Design Summary:"):
				summary_start = bufferno
				break
		if summary_start:
			output("""\n
**********************************************************************
* Design Summary                                                     *
**********************************************************************
""")
			for bufferno in range(summary_start-1, 0, -1):
				bufline = linesbuffer[bufferno]
				output("%s\n", bufline)
			output("%s\n", "*" * 70)

	######################################################################
	# Release 14.7 - par P.20131013 (lin64)                              #
	######################################################################

	if sline.startswith("Starting initial Timing Analysis"):
		summary_start = None
		for bufferno, bufline in enumerate(linesbuffer):
			sbufline = bufline.strip()
			if sbufline.startswith("Device Utilization Summary:"):
				summary_start = bufferno
				break
		if summary_start:
			output("""\n
**********************************************************************
* Device Utilization Summary                                         *
**********************************************************************
""")
			for bufferno in range(summary_start-1, 0, -1):
				bufline = linesbuffer[bufferno]
				output("%s\n", bufline)
			output("%s\n", "*" * 70)


	if sline.startswith("Phase"):
		if "REAL time:" in sline and not "unrouted" in sline:
			phase, rtime = sline.split("REAL time:")
			output(" (completed in %s)\n", rtime.strip())
		else:
			bits = sline.split()
			if keepalive_thread.last_output[-1] != '\n':
				output('\n')
			output("%5s %-5s - %s ", bits[0], bits[1], " ".join(bits[2:]))

	# Saving bit stream in 
	if sline.startswith("Saving bit stream in"):
		output("\n%s", sline)

	# If the line wasn't caught elsewhere, just output a dot.
	if not keepalive_thread.output:
		output(".")

for lineno, rawline in enumerate(sys.stdin.xreadlines()):
	output(rawline)

output("\n\n")
output("Raw output saved in %r\n", sys.argv[1])
