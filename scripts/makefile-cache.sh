#!/bin/bash

set -e

PLATFORMS=$(ls targets/ | grep -v ".py" | grep -v "common" | tr '\n' ' ' | sed -e"s+targets/++")

cat > build/cache.mk.tmp  <<EOF
# List of avaliable platforms
PLATFORMS = $PLATFORMS
EOF
for P in $PLATFORMS; do
	cat >> build/cache.mk.tmp <<EOF
# List of avaliable targets for $P
TARGETS_$P = $(ls targets/$P/ | grep ".py" | grep -v "__" | tr '\n' ' ' | sed -e"s+targets/$P/++" -e's/.py//g')
EOF
done

mv build/cache.mk.tmp build/cache.mk
