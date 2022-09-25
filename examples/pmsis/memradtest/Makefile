# User Test
#------------------------------------

ifndef MEM_LEVEL
MEM_LEVEL=1
endif

APP              = memradtest
# App sources
APP_SRCS         = memradtest.c
# App includes
APP_INC	         =
# Compiler flags
APP_CFLAGS       = -DMEM_LEVEL=$(MEM_LEVEL)
# Linker flags
APP_LDFLAGS      =

# Custom linker
APP_LINK_SCRIPT  =

include $(RULES_DIR)/pmsis_rules.mk
