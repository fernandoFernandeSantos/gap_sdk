#!/bin/bash

set -e

# Cleaning old files
rm -r logs/*

GAP_SDK_HOME=/home/fernando/git_research/gap_sdk

##### Setting the env
source $GAP_SDK_HOME/configs/gapuino_v2.sh

# Profiling
./profiler.py

# Injecting faults
./injector.py

exit 0