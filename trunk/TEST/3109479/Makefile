# PURPOSE: Makefile Demo Application of Quex
#
# ABSOLUTELY NO WARRANTY
#_______________________________________________________________________________
.PHONY: clean

ifndef QUEX_PATH
    $(error The environment variable QUEX_PATH is not defined!)
endif


CCFLAG_ASSERTS=-DQUEX_OPTION_ASSERTS

# (*) COMPILER SETTINGS ________________________________________________________
#     (change COMPILER to whatever you use as compiler on the command line,
#      e.g. "make COMPILER=icpc" will use intel's c++ compiler)
COMPILER = gcc -ggdb 

ifdef N
	QX_FILE=test$(N).qx
else
	QX_FILE=setting_of_N_not_specified_on_command_line_to_make
endif
	

CC = $(COMPILER) -c \
	 -I./ -I$(QUEX_PATH)                            \
	 -Wall -Werror -DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED -Wconversion -pedantic                   \
	 -DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED \
	 -DPRINT_TOKEN
     # -DQUEX_OPTION_DEBUG_SHOW \
	 $(CCFLAG_ASSERTS) 
     # -DQUEX_OPTION_ASSERTS_DISABLED
     # -DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED 
   
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

Simple.c: $(QX_FILE) 
	quex -i $(QX_FILE) -o Simple --language C --token-policy single #--debug-exception

# (*) HELPERS __________________________________________________________________
clean:	
	rm -f Simple*
	rm -f *.o
	rm -f *.bak
	rm -f *.E
	rm -f lexer
