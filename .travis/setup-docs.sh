#! /bin/bash

set -x
set -e

cd doc
make testenv
make wiki
make apidoc
