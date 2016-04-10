#!/bin/bash

set -e

# These must be outside the heredoc below otherwise the script won't error.
COMMIT="$(git log --format="%H" -n 1)"
BRANCH="$(git symbolic-ref --short HEAD)"
DESCRIBE="$(git describe --dirty)"

TMPFILE=$(tempfile)

cat > $TMPFILE <<EOF

const char* git_commit = "$COMMIT";
const char* git_branch = "$BRANCH";
const char* git_describe = "$DESCRIBE";
const char* git_status =
    "    --\n"
$(git status --short | sed -e's-^-   "    -' -e's-$-\\n"-')
    "    --\n";

EOF

if ! cmp -s $TMPFILE version_data.h; then
	echo "Updating version_data.h"
	mv $TMPFILE version_data.h
fi
