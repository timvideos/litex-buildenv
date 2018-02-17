#!/usr/bin/env python
"""
This file embeds in the firmware information like the git commit
number,git branch information and git status of the build tree.
"""

import subprocess
import os
import tempfile
import filecmp
import shutil

commit = subprocess.check_output(['git', 'log', '--format="%H"', '-n', '1'])\
                                    .decode('utf-8')
branch = subprocess.check_output(['git', 'symbolic-ref', '--short', 'HEAD'])\
                                    .decode('utf-8')
describe = subprocess.check_output(['git', 'describe', '--dirty'])\
                                    .decode('utf-8')
status = subprocess.check_output(['git', 'status', '--short']).decode('utf-8')
length = status.count('\n')

if "PLATFORM" in os.environ:
    platform = os.environ['PLATFORM']
else:
    platform = ""
    print("PLATFORM NOT SET")

if "TARGET" in os.environ:
    target = os.environ['TARGET']
else:
    target = ""
    print("TARGET NOT SET")

temp_h = tempfile.NamedTemporaryFile(suffix='.h', delete=True, mode='w+t')
print("Showing temp file .h")
print(temp_h.name)
string = ("""\
#ifndef __VERSION_DATA_H
#define __VERSION_DATA_H

extern const char* board;
extern const char* target;

extern const char* git_commit;
extern const char* git_branch;
extern const char* git_describe;
extern const char* git_status;

#endif  // __VERSION_DATA_H""")
temp_h.write(string)
temp_h.seek(0)

temp_c = tempfile.NamedTemporaryFile(suffix='.c', delete=True, mode='w+t')
print("Showing temp file .c")
print(temp_c.name)

string = ("""\

#ifndef PLATFORM_{}
#error "Version mismatch - PLATFORM_{} not defined!"
#endif
const char* board = "{}";

#ifndef TARGET_{}
#error "Version mismatch - TARGET_{} not defined!"
#endif
const char* target = "{}";

const char* git_commit = "{}";
const char* git_branch = "{}";
const char* git_describe = "{}";
const char* git_status =
    "    --\\r\\n"
""")

temp_c.write(string.format(platform.upper(), platform.upper(), platform,
             target.upper(), target.upper(), target, commit[1:-2],
             branch[:-1], describe[:-1]))

for line in range(0, length):
    temp = status.splitlines()[line]
    temp = '   "    ' + temp + '\\r\\n"'
    temp_c.write(temp)
    temp_c.write('\n')
temp_c.write('    "    --\\r\\n";')
temp_c.seek(0)


if not (filecmp.cmp(temp_h.name, 'version_data.h')):
    print("Updating version_data.h")
    os.remove('version_data.h')
    shutil.copyfile(temp_h.name, 'version_data.h')

if not (filecmp.cmp(temp_c.name, 'version_data.c')):
    print("Updating version_data.c")
    os.remove('version_data.c')
    shutil.copyfile(temp_c.name, 'version_data.c')
temp_c.close()
temp_h.close()
