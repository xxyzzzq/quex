# PURPOSE: Makefile Demo Application of Quex
#
# ABSOLUTELY NO WARRANTY
#_______________________________________________________________________________
.PHONY: clean

ifndef QUEX_PATH
    $(error The environment variable QUEX_PATH is not defined!)
endif

include $(QUEX_PATH)/quex/code_base/core.mkd

# (*) COMPILER SETTINGS ________________________________________________________
#     (change COMPILER to whatever you use as compiler on the command line,
#      e.g. "make COMPILER=icpc" will use intel's c++ compiler)
COMPILER = gcc # -ggdb # -Os

CC = $(COMPILER) -c \
	 -I./ -I$(QUEX_PATH)                             \
	 -Wall -Wconversion -pedantic                    \
	 $(CCFLAG_ASSERTS)                               \
	 -DPRINT_TOKEN                                   \
	 -DPRINT_LINE_COLUMN_NUMBER
     # -DQUEX_OPTION_ASSERTS_DISABLED
     # -DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED 
     # -D__QUEX_OPTION_DEBUG_STATE_TRANSITION_REPORTS
   
LD = $(COMPILER) 

# (*) RULES ____________________________________________________________________
# -- application
# Object files:
Case%: Case%.c 
	$(CC) $< -o $@ 

# Macro expansions (only for debugging):
%.E: %.c    
	$(CC) -E $< -o $@ 

Case%.c: case%.qx $(QUEX_CORE)
	quex -i $<  --engine $(@:.c=) --language C 

# (*) HELPERS __________________________________________________________________
clean:	
	rm -f Case*
	rm -f *.o
	rm -f *.bak
	rm -f *.E
	rm -f lexer
