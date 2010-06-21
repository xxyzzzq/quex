# PURPOSE: Makefile for unit tests.
#
# ABSOLUTELY NO WARRANTY
#_______________________________________________________________________________
.PHONY: clean
ifndef QUEX_PATH
    $(error The environment variable QUEX_PATH is not defined!)
endif
include $(QUEX_PATH)/quex/code_base/core.mkd

# (*) SETUP ____________________________________________________________________
# -- INPUT
MODE_FILES       = simple.qx
# -- FILES PRODUCED BY QUEX
ENGINE_NAME      = tiny_lexer# NOTE: a whitespace after this name creates chaos!
ENGINE_SOURCES   = $(ENGINE_NAME)                     \
                   $(ENGINE_NAME).c                 \
                   $(ENGINE_NAME)-token_ids           \
                   $(ENGINE_NAME)-configuration       
# -- OUTPUT
APPLICATION      = lexer

ifdef ASSERTS_ENABLED_F
	CCFLAG_ASSERTS=# By default asserts are enabled
else 
	CCFLAG_ASSERTS=-DQUEX_OPTION_ASSERTS_DISABLED
endif

# (*) COMPILER SETTINGS ________________________________________________________
#     (change COMPILER to whatever you use as compiler on the command line,
#     e.g. "make COMPILER=icpc" will use intel's c++ compiler)
COMPILER = gcc
CC = $(COMPILER) -c -ggdb -Wno-deprecated -Wall  \
	 -I./ -I$(QUEX_PATH) $(CCFLAG_ASSERTS)   \
     # -DQUEX_OPTION_ASSERTS_DISABLED
     # -DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED 


LD = $(COMPILER)

# (*) RULES ____________________________________________________________________
# -- application
$(APPLICATION): $(APPLICATION).o $(ENGINE_NAME).o 
	$(LD) $(APPLICATION).o $(ENGINE_NAME).o -o $(APPLICATION) 

# -- engine and object files
%.o: %.c $(ENGINE_SOURCES)
	$(CC) $< -o $@

example.o: ../example.c  EasyLexer.c
	$(CC) $< -o $@ 

EasyLexer EasyLexer.c: $(MODE_FILES) $(QUEX_CORE)
	quex -i $(MODE_FILES) --engine $(ENGINE_NAME) --token-policy single \
		 --language C

# (*) HELPERS __________________________________________________________________
#
clean:	
	touch $(MODE_FILES)
	rm -f EasyLexer-token EasyLexer-configuration
	rm -f $(ENGINE_NAME)-token
	rm -f $(ENGINE_NAME).o
	rm -f lexer.o
	rm -f lexer
	rm -f token_ids
	rm -f *.bak
