#!/usr/bin/env python3

import os.path
import shutil
import sys

d = sys.argv[1]
assert d, d

for l in sys.stdin.readlines():
    src = l.strip()
    assert src, src
    assert src.startswith('/'), src
    out = os.path.join(d, src[1:])
    outdir = os.path.dirname(out)
    src = src.replace('/opt/Xilinx/', '/opt/Xilinx.real/')
    if not os.path.exists(outdir):
        os.makedirs(outdir)
        print("New pdir {}".format(outdir))

    if os.path.isdir(src):
        os.makedirs(out, exist_ok=False)
        shutil.copystat(src, out)
        print("New dir  {}".format(out))
    else:
        shutil.copy2(src, out, follow_symlinks=False)
        print("New file {} -> {}".format(src, out))
