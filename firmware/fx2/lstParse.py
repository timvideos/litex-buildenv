#!/usr/bin/env python
#
# Copyright (C) 2014 Chris McClelland
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
import fileinput
import re

tdoList = []
tdiList = []
tmsList = []
tckList = []
ioaList = []

for line in fileinput.input():
  m = re.search(r"^\s+([0-9A-F]+)\s+(A2|30) B0 (  |0C)\s+(\[\d+\]\s+)?\d+[^;]+_TDO.*?$", line)
  if ( m != None ):
    tdoList.append("0x{:04X}".format(1 + int(m.group(1), 16)))
  m = re.search(r"^\s+([0-9A-F]+)\s+92 B1\s+(\[\d+\]\s+)?\d+[^;]+_TDI.*?$", line)
  if ( m != None ):
    tdiList.append("0x{:04X}".format(1 + int(m.group(1), 16)))
  m = re.search(r"^\s+([0-9A-F]+)\s+[9D]2 B2\s+(\[\d+\]\s+)?\d+[^;]+_TMS.*?$", line)
  if ( m != None ):
    tmsList.append("0x{:04X}".format(1 + int(m.group(1), 16)))
  m = re.search(r"^\s+([0-9A-F]+)\s+[CD]2 B3\s+(\[\d+\]\s+)?\d+[^;]+_TCK.*?$", line)
  if ( m != None ):
    tckList.append("0x{:04X}".format(1 + int(m.group(1), 16)))
  m = re.search(r"^\s+([0-9A-F]+)\s+85 9C 80", line)
  if ( m != None ):
    ioaList.append("0x{:04X}".format(2 + int(m.group(1), 16)))

print("// THIS FILE IS MACHINE-GENERATED! DO NOT EDIT IT!\n//")

if ( len(ioaList) != 1 ):
  print("ERROR: There must be exactly one occurrence of IOA!")
  exit(1)

print("static const uint16 ioaList[] = {{\n\t{},\n\t0x0000\n}};\n".format(ioaList[0]));

print("static const uint16 tdoList[] = {")
for i in tdoList:
  print("\t{},".format(i))
print("\t0x0000\n};\n")

print("static const uint16 tdiList[] = {")
for i in tdiList:
  print("\t{},".format(i))
print("\t0x0000\n};\n")

print("static const uint16 tmsList[] = {")
for i in tmsList:
  print("\t{},".format(i))
print("\t0x0000\n};\n")

print("static const uint16 tckList[] = {")
for i in tckList:
  print("\t{},".format(i))
print("\t0x0000\n};")
