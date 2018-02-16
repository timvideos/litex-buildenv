#!/usr/bin/env python

import subprocess
import os
import tempfile
import filecmp
import shutil

commit = subprocess.check_output(['git', 'log', '--format="%H"', '-n', '1'])
print ("Showing commit variable")
print (commit[1:-2])

branch = subprocess.check_output(['git', 'symbolic-ref', '--short', 'HEAD'])
print ("Showing branch variable")
print (branch[:-1])

describe = subprocess.check_output(['git', 'describe', '--dirty'])
print ("Showing describe variable")
print (describe[:-1])

status = subprocess.check_output(['git', 'status', '--short'])
length = status.count(b'\n')
print (status)

print ("Showing uplatform")
if "PLATFORM" in os.environ:
    platform = os.environ['PLATFORM']
    print (platform.upper())
else:
    platform = ""

print ("Showing utarget")
if "TARGET" in os.environ:
    target = os.environ['TARGET']
    print (target.upper())
else:
    target = ""

temp_h = tempfile.NamedTemporaryFile(suffix='.h', delete='true')
print ("Showing temp file .h")
print (temp_h.name)
temp_h.write(b"""\
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


temp_c = tempfile.NamedTemporaryFile(suffix='.c', delete='true')
print ("Showing temp file .c")
print (temp_c.name)

temp_c.write(b"""\

#ifndef PLATFORM_%s
#error \"Version mismatch - PLATFORM_%s not defined!\"
#endif
const char* board = \"%s\";

#ifndef TARGET_%s
#error \"Version mismatch - TARGET_%s not defined!\"
#endif
const char* target = \"%s\";

const char* git_commit = \"%s\";
const char* git_branch = \"%s\";
const char* git_describe = \"%s\";
const char* git_status =
    \"    --\\r\\n\"
""" % (platform.upper().encode(), platform.upper().encode(), platform.encode(),
       target.upper().encode(), target.upper().encode(), target.encode(),
       commit[1:-2], branch[:-1], describe[:-1]))

for x in range(0, length):
    temp = status.splitlines()[x]
    temp = '   "    ' + temp.decode() + '\\r\\n"'
    temp_c.write(temp.encode())
    temp_c.write(b'\n')
temp_c.write(b'    "    --\\r\\n";')
temp_c.seek(0)


if not (filecmp.cmp(temp_h.name, 'version_data.h')):
    print ("Updating version_data.h")
    os.remove('version_data.h')
    shutil.copyfile(temp_h.name, 'version_data.h')

if not (filecmp.cmp(temp_c.name, 'version_data.c')):
    print ("Updating version_data.c")
    os.remove('version_data.c')
    shutil.copyfile(temp_c.name, 'version_data.c')
temp_c.close()
temp_h.close()
