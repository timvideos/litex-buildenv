#!/bin/bash
cat > version_data.h <<EOF

const char* git_commit = "$(git log --format="%H" -n 1)";
const char* git_branch = "$(git symbolic-ref --short HEAD)";
const char* git_describe = "$(git describe --dirty)";
const char* git_status =
    "    --\n"
$(git status --short | sed -e's-^-   "    -' -e's-$-\\n"-')
    "    --\n";

EOF
