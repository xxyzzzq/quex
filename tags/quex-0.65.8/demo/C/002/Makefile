# PURPOSE: Makefile Demo Application of Quex
#
# ABSOLUTELY NO WARRANTY
#_______________________________________________________________________________
.PHONY: clean

ifndef QUEX_PATH
    $(error The environment variable QUEX_PATH is not defined!)
endif

ifdef ASSERTS_ENABLED_F
	CCFLAG_ASSERTS=# By default asserts are enabled
else 
	CCFLAG_ASSERTS=-DQUEX_OPTION_ASSERTS_DISABLED
endif

# (*) COMPILER SETTINGS ________________________________________________________
COMPILER := gcc -Wall -Werror -Wconversion -pedantic # -ggdb 

CC := $(COMPILER) -I./ -I$(QUEX_PATH) $(CCFLAG_ASSERTS) \
      -DPRINT_LINE_COLUMN_NUMBER                        \
      -DPRINT_TOKEN                                     \
      -DQUEX_SETTING_TOKEN_QUEUE_SIZE=10                \
      -DQUEX_SETTING_TOKEN_QUEUE_SAFETY_BORDER=4      

# Useful Debugging Options:
# -DQUEX_OPTION_DEBUG_SHOW \
# -DQUEX_OPTION_ASSERTS_DISABLED
# -DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED \
# -DQUEX_OPTION_DEBUG_SHOW

# (*) RULES ____________________________________________________________________
#
all:   lexer lexer2

lexer: simple.qx
	quex -i patterns.qx tokens.qx simple.qx -o EasyLexer --language C
	$(CC) -o $@ ../example.c EasyLexer.c 
         
lexer2: simple2.qx
	quex -i patterns.qx tokens.qx simple2.qx -o EasyLexer --language C
	$(CC) -o $@ ../example.c EasyLexer.c 

# (*) HELPERS __________________________________________________________________
#

%.E: %.c
	$(CC) -E $< -o $@ 

clean:	
	rm -f EasyLexer*
	rm -f *.o
	rm -f *.bak
	rm -f *.E
	rm -f lexer lexer2
