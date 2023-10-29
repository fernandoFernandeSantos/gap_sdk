#!/bin/bash
# Command necessary to run the application from GAPY
gapy --target=gapuino_v2 --platform=gvsoc --work-dir=/home/carol/gap_sdk/examples/autotiler/Mnist/BUILD/GAP8_V2/GCC_RISCV_PULPOS \
  --config-opt=**/runner/boot/mode=flash run --exec-prepare \
  --exec --binary=/home/carol/gap_sdk/examples/autotiler/Mnist/BUILD/GAP8_V2/GCC_RISCV_PULPOS/Mnist >"${STDOUT_FILE}" 2>"${STDERR_FILE}"

# Limit the amount of info that it can print
sed -i '1000,$d' "${STDOUT_FILE}"
sed -i '1000,$d' "${STDERR_FILE}"