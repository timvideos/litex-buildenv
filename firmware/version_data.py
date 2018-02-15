import  subprocess
import  os
import  tempfile
import  filecmp
import  shutil

commit          = subprocess.Popen(['git', 'log', '--format="%H"', '-n''1'], stdout=subprocess.PIPE)
commit,gar      = commit.communicate()
print   "Showing commit variable"
print   commit[1:-2]

branch          = subprocess.Popen(['git', 'symbolic-ref', '--short', 'HEAD'], stdout=subprocess.PIPE)
branch,gar      = branch.communicate()
print   "Showing branch variable"
print   branch[:-1]

describe        = subprocess.Popen(['git', 'describe', '--dirty'], stdout=subprocess.PIPE)
describe,gar    = describe.communicate();
print   "Showing describe variable"
print describe[:-1]

status          = subprocess.Popen(['git', 'status', '--short'], stdout=subprocess.PIPE)
status,gar      = status.communicate();

platform        = os.environ['PLATFORM']
print   "Showing uplatform"
print   platform.upper()

target          = os.environ['TARGET']
print   "Showing utarget"
print   target.upper()

temp_h          = tempfile.NamedTemporaryFile( suffix='.h',delete='true')
print   "Showing temp file .h"
print   temp_h.name
temp_h.write    ('#ifndef   __VERSION_DATA_H\n'         )
temp_h.write    ('#define   __VERSION_DATA_H\n'         )
temp_h.write    ('\n'                                   )
temp_h.write    ('extern const char* board;\n'          )
temp_h.write    ('extern const char* target;\n'         )
temp_h.write    ('\n'                                   )
temp_h.write    ('extern const char* git_commit;\n'     )
temp_h.write    ('extern const char* git_branch;\n'     )
temp_h.write    ('extern const char* git_describe;\n'   )
temp_h.write    ('extern const char* git_status;\n'     )
temp_h.write    ('\n'                                   )
temp_h.write    ('#endif  // __VERSION_DATA_H\n'        )
temp_h.seek(0)

temp_c          = tempfile.NamedTemporaryFile( suffix='.c',delete='true')
print   "Showing temp file .c"
print   temp_c.name
temp_c.write    ('#ifndef PLATFORM_'                    )
temp_c.write    (platform                               )
temp_c.write    ('\n'                                   )
temp_c.write    ('#error "Version mismatch - PLATFORM_' )
temp_c.write    (platform                               )
temp_c.write    (' not defined!"'                       )
temp_c.write    ('\n'                                   )
temp_c.write    ('#endif'                               )
temp_c.write    ('\n'                                   )
temp_c.write    ('\n'                                   )
temp_c.write    ('const char* board = "'                )
temp_c.write    (platform                               )
temp_c.write    ('";'                                   )
temp_c.write    ('\n'                                   )

temp_c.write    ('#ifndef TARGET_'                      )
temp_c.write    (target                                 )
temp_c.write    ('\n'                                   )
temp_c.write    ('#error "Version mismatch - TARGET_'   )
temp_c.write    (target                                 )
temp_c.write    (' not defined!"'                       )
temp_c.write    ('\n'                                   )
temp_c.write    ('#endif'                               )
temp_c.write    ('\n'                                   )
temp_c.write    ('\n'                                   )
temp_c.write    ('const char* target = "'               )
temp_c.write    (target                                 )
temp_c.write    ('";'                                   )
temp_c.write    ('\n'                                   )

temp_c.write    ('const char* git_commit = "'           )
temp_c.write    (commit[1:-2]                           )
temp_c.write    ('";'                                   )
temp_c.write    ('\n'                                   )
temp_c.write    ('const char* git_branch = "'           )
temp_c.write    (branch[:-1]                            )
temp_c.write    ('";'                                   )
temp_c.write    ('\n'                                   )
temp_c.write    ('const char* git_describe = "'         )
temp_c.write    (describe[:-1]                          )
temp_c.write    ('";'                                   )
temp_c.write    ('\n'                                   )

temp_c.write    ('const char* git_status =\n'             )
temp_c.write    ('    "    --\\r\\n"\n')

for x in range ( 0, len(status.split('\n'))-1 ):
    temp    = status.splitlines()[x]
    temp    = '   "    ' + temp + '\\r\\n"'
    temp_c.write    (temp)
    temp_c.write    ('\n')
temp_c.write    ('    "    --\\r\\n";')
temp_c.seek(0)

if not ( filecmp.cmp(temp_h.name,'version_data.h') ):
    print   "Updating version_data.h"
    os.remove       ('version_data.h')
    shutil.copyfile (temp_h.name,'version_data.h')

if not ( filecmp.cmp(temp_c.name,'version_data.c') ):
    print   "Updating version_data.c"
    os.remove       ('version_data.c')
    shutil.copyfile (temp_c.name,'version_data.c')
temp_c.close()
temp_h.close()
