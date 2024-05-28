# User Test
#------------------------------------

MEM_LEVEL=1
#SET_VALUE=0xAAAAAAAA
SET_VALUE=0xFFFFFFFF
#SET_VALUE=0

APP              = memradtest
# App sources
APP_SRCS         = memradtest.c
# App includes
APP_INC	         =
# Compiler flags
APP_CFLAGS       = -DMEM_LEVEL=$(MEM_LEVEL) -DSET_VALUE=$(SET_VALUE)
# Linker flags
APP_LDFLAGS      =

# Custom linker
APP_LINK_SCRIPT  =

include $(RULES_DIR)/pmsis_rules.mk
