#!/bin/bash

GAP_SDK_PATH=/home/fernando/git_research/gap_sdk
APP_PATH="${GAP_SDK_PATH}/examples/gap8/nn/autotiler/Mnist"

# Command necessary to run the application from GAPY
gapy --target=gapuino_v3 --platform=gvsoc --work-dir="${APP_PATH}"/BUILD/GAP8_V3/GCC_RISCV \
--config-opt=**/runner/boot/mode=flash run --exec-prepare \
--exec --binary="${APP_PATH}"/BUILD/GAP8_V3/GCC_RISCV/Mnist >"${STDOUT_FILE}" 2>"${STDERR_FILE}"

# Limit the amount of info that it can print
sed -i '1000,$d' "${STDOUT_FILE}"
sed -i '1000,$d' "${STDERR_FILE}"