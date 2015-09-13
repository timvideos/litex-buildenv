#!/bin/bash

set -x
set -e

sudo apt-get install -y realpath

# Run the script once to check it works
time scripts/get-env.sh
# Run the script again to check it doesn't break things
time scripts/get-env.sh

set +x
set +e
. scripts/setup-env.sh
