#!/bin/bash

WORKSPACE="$( cd "$(dirname "$0")" ; pwd -P )/build"

./install.sh $WORKSPACE

pushd $WORKSPACE
python3 ../execute_tests.py 
popd
