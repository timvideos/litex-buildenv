#!/bin/bash

set -e

# These must be outside the heredoc below otherwise the script won't error.
COMMIT="$(git log --format="%H" -n 1)"
BRANCH="$(git symbolic-ref --short HEAD)"
DESCRIBE="$(git describe --dirty)"

TMPFILE_H=$(tempfile -s .h)
TMPFILE_C=$(tempfile -s .c)

UBOARD="$(echo $BOARD | tr '[:lower:]' '[:upper:]')"
UTARGET="$(echo $TARGET | tr '[:lower:]' '[:upper:]')"

cat > $TMPFILE_H <<EOF
#ifndef __VERSION_DATA_H
#define __VERSION_DATA_H

extern const char* board;
extern const char* target;

extern const char* git_commit;
extern const char* git_branch;
extern const char* git_describe;
extern const char* git_status;

#endif  // __VERSION_DATA_H
EOF

cat > $TMPFILE_C <<EOF

#ifndef BOARD_$UBOARD
#error "Version mismatch - BOARD_$UBOARD not defined!"
#endif
const char* board = "$BOARD";

#ifndef TARGET_$UTARGET
#error "Version mismatch - TARGET_$UTARGET not defined!"
#endif
const char* target = "$TARGET";

const char* git_commit = "$COMMIT";
const char* git_branch = "$BRANCH";
const char* git_describe = "$DESCRIBE";
const char* git_status =
    "    --\n"
$(git status --short | sed -e's-^-   "    -' -e's-$-\\n"-')
    "    --\n";

EOF

if ! cmp -s $TMPFILE_H version_data.h; then
	echo "Updating version_data.h"
	mv $TMPFILE_H version_data.h
fi

if ! cmp -s $TMPFILE_C version_data.c; then
	echo "Updating version_data.c"
	mv $TMPFILE_C version_data.c
fi
