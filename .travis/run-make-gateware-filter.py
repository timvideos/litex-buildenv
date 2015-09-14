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

log_file = open(sys.argv[1], 'w')

# Suppressions for warning / info messages
suppressions = [x.strip() for x in open(sys.argv[2], 'r').readlines() if not x.startswith('#')]
pprint.pprint(suppressions)
suppressions = [re.compile(x) for x in suppressions]

top_path = os.path.normpath(os.getcwd())

def output(s, *args, **kw):
	keepalive_thread.output = True
	if args:
		assert not kw
		sys.stdout.write((s % args).encode('utf-8'))
	elif kw:
		sys.stdout.write((s % kw).encode('utf-8'))
	else:
		sys.stdout.write(s.encode('utf-8'))

	# Flush every second
	if (time.time() - keepalive_thread.last_output_time) > 1:
		sys.stdout.flush()

	keepalive_thread.last_output_time = time.time()


class KeepAliveThread(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
		self.daemon = True
		self.output = False
		self.last_output_time = time.time()

	def run(self):
		while True:
			if (time.time() - self.last_output_time) > 30:
				output(u"\U0001F436")
			time.sleep(1)

keepalive_thread = KeepAliveThread()
keepalive_thread.start()

BUFFER_SIZE=100
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
for lineno, rawline in enumerate(sys.stdin.readlines()):
	log_file.write(rawline+'\n')
	log_file.flush()

	line = rawline.strip('\n\r')
	sline = line.strip()
	linesbuffer.appendleft(line)
	while len(linesbuffer) > BUFFER_SIZE:
		linesbuffer.pop()

	if line.startswith("make"):
		output('\n'+line+'\n')
		continue

	if not sline:
		continue

	if line.startswith("ERROR:"):
		output("\nError detected! - %s\n%s\n%s\n%s\n", line, ERROR, "\n".join(reversed(linesbuffer)), ERROR)
		continue

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
			output("\n\n%s\n%s\n%s\n", linesbuffer[0], linesbuffer[1], linesbuffer[2])
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
			if bufferno == 0:
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
			output("\n")
			for i in range(summary_start, 0, -1):
				output("%s\n", linesbuffer[i])

	#########################################################################
	# 2) HDL Parsing
	# -----------------------------------------------------------------------
	# Analyzing Verilog file "/home/tansell/foss/timvideos/hdmi2usb/HDMI2USB-misoc-firmware/build/misoc/extcores/lm32/submodule/rtl/lm32_dtlb.v" into library work
	ANALYZING_VERILOG = "Analyzing Verilog"
	if sline.startswith(ANALYZING_VERILOG):
		output("\n\n%s ", shorten_path(sline))
	
	# Parsing package <MDCT_PKG>.
	# Parsing module <lm32_addsub>.
	# Parsing entity <ByteStuffer>.
	# Parsing architecture <RTL> of entity <bytestuffer>.
	PARSING = "Parsing "
	if sline.startswith(PARSING):
		if sline.startswith("Parsing VHDL"):
			output("\n\n%s ", shorten_path(sline))
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
			found_specials = []
			output("    %s\n", "--")
			for bufferno in range(summary_start-1, 0, -1):
				sbufline = linesbuffer[bufferno].strip()
				output("    %s\n", sbufline[0].upper()+sbufline[1:-1])
		output("\n")

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
		output("\n\n%s\n" % sline)
	

	#########################################################################
	# 7) Partition Report
	# -----------------------------------------------------------------------
	
	# Nothing?

	#########################################################################
	# 8) Design Summary
	# -----------------------------------------------------------------------

	# If the line wasn't caught elsewhere, just output a dot.
	if not keepalive_thread.output:
		output(".")
