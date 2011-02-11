# PURPOSE: Makefile Demo Application of Quex
#
# ABSOLUTELY NO WARRANTY
#_______________________________________________________________________________
.PHONY: clean

include $(QUEX_PATH)/quex/code_base/core.mkd

# (*) COMPILER SETTINGS ________________________________________________________
#     (change COMPILER to whatever you use as compiler on the command line,
#      e.g. "make COMPILER=icpc" will use intel's c++ compiler)
COMPILER = g++ -ggdb 

CC = $(COMPILER) -c \
	 -I./ -I$(QUEX_PATH)              \
	 -Wall -Wconversion -pedantic     \
	 $(CCFLAG_ASSERTS) 
   
LD = $(COMPILER) 

# (*) RULES ____________________________________________________________________
# -- application
lexer:          lexer.o EasyLexer.o
	$(LD) -o $@ lexer.o EasyLexer.o 
          
# Object files:
%.o: %.cpp EasyLexer
	$(CC) $< -o $@ 

# Macro expansions (only for debugging):
%.E: %.cpp    
	$(CC) -E $< -o $@ 

EasyLexer EasyLexer.cpp: example.qx $(QUEX_CORE)
	quex -i  example.qx  --engine  EasyLexer --token-policy single


# (*) HELPERS __________________________________________________________________
clean:	
	rm -f EasyLexer*
	rm -f *.o
	rm -f *.bak
	rm -f *.E
	rm -f lexer
