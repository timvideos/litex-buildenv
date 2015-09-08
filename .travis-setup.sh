#!/bin/bash

set -x
set -e
df -h

sudo apt-get install -y realpath

scripts/get-env.sh
. scripts/setup-env.sh
