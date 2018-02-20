#!/usr/bin/env python
"""
This file embeds in the firmware information like the git commit
number, git branch information and git status of the build tree.
"""

import subprocess
import os
import sys
import io

commit = subprocess.check_output(
        ['git', 'log', '--format="%H"', '-n', '1']).decode('utf-8')
branch = subprocess.check_output(
        ['git', 'symbolic-ref', '--short', 'HEAD']).decode('utf-8')
describe = subprocess.check_output(
        ['git', 'describe', '--dirty']).decode('utf-8')
status = subprocess.check_output(['git', 'status', '--short']).decode('utf-8')
length = status.count('\n')

if "PLATFORM" in os.environ:
    platform = os.environ['PLATFORM']
else:
    sys.stderr.write("""\
    PLATFORM environment variable is not set.

    This script should only be run as part of LiteX Build Environment.

    Try 'source ./scripts/enter-env.sh'
""")
    sys.exit(1)

if "TARGET" in os.environ:
    target = os.environ['TARGET']
else:
    sys.stderr.write("""\
    TARGET environment variable is not set.

    This script should only be run as part of LiteX Build Environment

    Try 'source ./scripts/enter-env.sh'
""")
    sys.exit(1)

temp_h = io.StringIO()
temp_h.write("""\
#ifndef __VERSION_DATA_H
#define __VERSION_DATA_H

extern const char* board;
extern const char* target;

extern const char* git_commit;
extern const char* git_branch;
extern const char* git_describe;
extern const char* git_status;

#endif  // __VERSION_DATA_H""")
temp_h.seek(0)

temp_c = io.StringIO()
temp_c.write("""\
#ifndef PLATFORM_{UPLATFORM}
#error "Version mismatch - PLATFORM_{UPLATFORM} not defined!"
#endif
const char* board = "{PLATFORM}";

#ifndef TARGET_{UTARGET}
#error "Version mismatch - TARGET_{UTARGET} not defined!"
#endif
const char* target = "{TARGET}";

const char* git_commit = "{COMMIT}";
const char* git_branch = "{BRANCH}";
const char* git_describe = "{DESCRIBE}";
const char* git_status =
    "    --\\r\\n"
""".format(UPLATFORM=platform.upper(), PLATFORM=platform,
           UTARGET=target.upper(), TARGET=target,
           COMMIT=commit[1:-2], BRANCH=branch[:-1], DESCRIBE=describe[:-1]))

for line in range(0, length):
    temp = status.splitlines()[line]
    temp = '   "    ' + temp + '\\r\\n"'
    temp_c.write(temp)
    temp_c.write('\n')
temp_c.write('    "    --\\r\\n";')
temp_c.seek(0)

try:
    myfile = open("version_data.c", "r+")
except IOError:
    myfile = open("version_data.c", "w+")
data = myfile.read()
data_c = temp_c.getvalue()
if not (dat a == data_c):
    print("Updating version_data.c")
    myfile.seek(0)
    myfile.truncate(0)
    myfile.write(data_c)
myfile.close()

try:
    myfile = open("version_data.h", "r+")
except IOError:
    myfile = open("version_data.h", "w+")
data = myfile.read()
data_h = temp_h.getvalue()
if not (data == data_h):
    print("Updating version_data.h")
    myfile.seek(0)
    myfile.truncate(0)
    myfile.write(data_h)
myfile.close()

temp_c.close()
temp_h.close()
