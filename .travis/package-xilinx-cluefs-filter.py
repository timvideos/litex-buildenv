#! /usr/bin/env python

import os
import csv
import sys

with open(sys.argv[1]) as csvfile:
    # 2017-10-15T09:24:17.147577188Z,2017-10-15T09:24:17.147595641Z,18453,tim,1001,tim,1001,/bin/ls,14308,/opt/Xilinx.real,dir,open,O_RDONLY,0000,4096,4096,1
    reader = csv.DictReader(
        csvfile,
        fieldnames=(
            "start_ts",
            "end_ts",
            "duration_ns", # nanoseconds
            "user",
            "uid",
            "group",
            "gid",
            "process",
            "pid",
            "path",
            "type"),
    )

    paths = set()
    for l in reader:
        #print(l)
        #if l['type'] != 'file':
        #    continue
        if not l['path'].startswith('/opt/Xilinx'):
            continue
        if not os.path.exists(l['path']):
            continue
        #if os.path.isdir(l['path']):
        #    continue

        src = l['path']
        dst = l['path'].replace('/opt/Xilinx.real/', '/opt/Xilinx/')

        paths.add(dst)

for p in sorted(paths):
    print(p)
