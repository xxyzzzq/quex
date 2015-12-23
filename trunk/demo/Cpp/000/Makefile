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
#     (change COMPILER to whatever you use as compiler on the command line,
#      e.g. "make COMPILER=icpc" will use intel's c++ compiler)
COMPILER   = g++ -ggdb -pedantic -Wconversion -Wall -Werror -W

CC = $(COMPILER) -c -I./ -I$(QUEX_PATH) $(CCFLAG_ASSERTS) 
# Other useful options for debugging:
# -DQUEX_OPTION_ASSERTS_DISABLED
# -DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED 
# -DQUEX_OPTION_DEBUG_SHOW
   
LD = $(COMPILER) 

# (*) RULES ____________________________________________________________________
#
lexer:          example.o EasyLexer.o
	$(LD) -o $@ example.o EasyLexer.o 
          
EasyLexer.o: EasyLexer.cpp 
	$(CC) $< -o $@ 

example.o: ../example.cpp EasyLexer.cpp
	$(CC) $< -o $@ 

EasyLexer.cpp: simple.qx 
	quex -i                 simple.qx  \
	     -o                 EasyLexer  \
		 --token-id-offset  0x1000

# (*) HELPERS __________________________________________________________________
#
source-package:
	quex -i                 simple.qx  \
	     -o                 EasyLexer  \
		 --token-id-offset  0x1000     \
		 --post-categorizer            \
		 --source-package   lexer_mine

# Macro expansions (only for debugging):
%.E: %.cpp    
	$(CC) -E $< -o $@ 

clean:	
	rm -f EasyLexer*
	rm -f *.o
	rm -f *.bak
	rm -f *.E
	rm -f lexer
