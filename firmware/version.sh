#!/bin/bash
cat > version.h <<EOF

#ifndef __VERSION_H
#define __VERSION_H

const char* git_commit = "$(git log --format="%H" -n 1)";
const char* git_describe = "$(git describe --dirty)";
const char* git_status =
    "    --\n"
$(git status --short | sed -e's-^-   "    -' -e's-$-\\n"-')
    "    --\n";

#endif // __VERSION_H
EOF
