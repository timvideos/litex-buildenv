#!/bin/bash

set -x
set -e

sudo apt-get install -y realpath

scripts/get-env.sh

set +x
set +e
. scripts/setup-env.sh
