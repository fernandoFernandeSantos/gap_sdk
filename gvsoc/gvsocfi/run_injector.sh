#!/bin/bash

set -e

# Cleaning old files
rm -rf logs/*

GAP_SDK_HOME=/home/fernando/git_research/gap_sdk

##### Setting the env
source $GAP_SDK_HOME/configs/gapuino_v3.sh

FAULT_SITES=(
  GVSOCFI_MEM_RUN_TYPE
  GVSOCFI_RUN_TYPE
)

for fault_site in "${FAULT_SITES[@]}"; do
  # Profiling
  ./profiler.py --fault_site "${fault_site}"

  # Injecting faults
  ./injector.py --fault_site "${fault_site}"
done

exit 0
