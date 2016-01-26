import binascii
import os
import subprocess

from migen.fhdl.std import *
from migen.bank.description import *

def git_root():
    return subprocess.check_output(
        "git rev-parse --show-toplevel",
        shell=True,
        cwd=os.path.dirname(__file__),
    ).decode('ascii').strip() 

def git_commit():
    data = subprocess.check_output(
        "git rev-parse HEAD",
        shell=True,
        cwd=git_root(),
    ).decode('ascii').strip()
    return binascii.unhexlify(data)

def git_describe():
    return subprocess.check_output(
        "git describe --dirty",
        shell=True,
        cwd=git_root(),
    ).decode('ascii').strip()

def git_status():
    return subprocess.check_output(
        "git status --short",
        shell=True,
        cwd=git_root(),
    ).decode('ascii').strip()


class GitInfo(Module, AutoCSR):
    def __init__(self):
        commit = sum(int(x) << (i*8) for i, x in enumerate(reversed(git_commit())))
        self.commit = CSRStatus(160)

	# FIXME: This should be a read-only Memory object
        #extradata = [ord(x) for x in "\0".join([
        #    "https://github.com/timvideos/HDMI2USB-misoc-firmware.git",
        #    git_describe(),
        #    git_status(),
        #    "",
        #    ])]
        #self.extradata = CSRStatus(len(extradata)*8)

        self.comb += [
            self.commit.status.eq(commit),
        #    self.extradata.status.eq(extradata),
        ]
