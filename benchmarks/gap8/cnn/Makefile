# Copyright (C) 2017 ETH Zurich, University of Bologna and GreenWaves Technologies
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the BSD license.  See the LICENSE file for details.
#//    ---------------        Sequential   ---------------
#//    i 0 j 0 cur test 0 --                 2x2/2 Max Pool Input: 112x112
#//    i 1 j 0 cur test 1 --                 2x2/2 Avg Pool Input: 112x112
#//    i 2 j 0 cur test 2 --               5x5 Convolutions Input: 112x112
#//    i 3 j 0 cur test 3 --                         Linear Input: 1024x16
#//    ---------------   Parallel Vector   ---------------
#//    i 0 j 3 cur test 14 --                 2x2/2 Max Pool Input: 112x112
#//    i 1 j 3 cur test 15 --                 2x2/2 Avg Pool Input: 112x112
#//    i 2 j 3 cur test 16 --               5x5 Convolutions Input: 112x112
#//    i 3 j 3 cur test 17 --                         Linear Input: 1024x16
ifndef RAD_CNN_OP
RAD_CNN_OP=2
endif

PULP_APP = cnnOps
PULP_APP_FC_SRCS = AllTest.c
PULP_CFLAGS = -O2 -g -DRAD_CNN_OP=$(RAD_CNN_OP)

#RISCV STD ISA
#RISCV_FLAGS = -march=rv32imc -DRISCV

#RISCV STD ISA + GAP8 Extensions
RISCV_FLAGS ?= -march=rv32imcxgap8


RISCV_FLAGS += -mPE=8 -mFC=1 -D__riscv__

include $(GAP_SDK_HOME)/utils/rules/pulp_rules.mk