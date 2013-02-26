# PURPOSE: Makefile Demo Application of Quex
#
# ABSOLUTELY NO WARRANTY
#_______________________________________________________________________________
.PHONY: clean

ifndef QUEX_PATH
    $(error The environment variable QUEX_PATH is not defined!)
endif

include $(QUEX_PATH)/quex/code_base/core.mkd

ifeq ($(QX_FILE),example.qx)
	ADD_DEFINES=-DQUEX_SETTING_BUFFER_SIZE=8
else
	ADD_DEFINES=-DQUEX_SETTING_BUFFER_SIZE=11 -DPRINT_LINE_COLUMN_NUMBER
endif

CCFLAG_ASSERTS=-DQUEX_OPTION_ASSERTS

# (*) COMPILER SETTINGS ________________________________________________________
#     (change COMPILER to whatever you use as compiler on the command line,
#      e.g. "make COMPILER=icpc" will use intel's c++ compiler)
COMPILER = gcc -ggdb 

CC = $(COMPILER) -c \
	 -I./ -I$(QUEX_PATH)                            \
	 -Wall -Wconversion -pedantic                   \
	 -DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED \
	 -DPRINT_TOKEN                                  \
	 $(ADD_DEFINES)
   
LD = $(COMPILER) 

# (*) RULES ____________________________________________________________________
# -- application
lexer:          example.o Simple.o
	$(LD) -o $@ example.o Simple.o 
          
# Object files:
Simple.o: Simple.c 
	$(CC) $< -o $@ 

example.o: $(QUEX_PATH)/TEST/lexer.c  Simple.c
	$(CC) $< -o $@ 

# Macro expansions (only for debugging):
%.E: %.c    
	$(CC) -E $< -o $@ 

Simple.c: $(QX_FILE) $(QUEX_CORE)
	quex -i $(QX_FILE) --engine Simple --language C --token-policy single --debug-exception

# (*) HELPERS __________________________________________________________________
clean:	
	rm -f Simple*
	rm -f *.o
	rm -f *.bak
	rm -f *.E
	rm -f lexer
