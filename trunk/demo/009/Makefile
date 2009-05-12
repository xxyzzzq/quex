# PURPOSE: Makefile Demo Application of Quex
#
# ABSOLUTELY NO WARRANTY
#_______________________________________________________________________________
.PHONY: clean

ifndef QUEX_PATH
    $(error The environment variable QUEX_PATH is not defined!)
endif

include $(QUEX_PATH)/quex/code_base/core.mkd

# (*) SETUP ____________________________________________________________________
SOURCES  = tiny_lexer  tiny_lexer.cpp  tiny_lexer-token_ids  tiny_lexer-core-engine.cpp

# (*) COMPILER SETTINGS ________________________________________________________
#     (change COMPILER to whatever you use as compiler on the command line,
#      e.g. "make COMPILER=icpc" will use intel's c++ compiler)
COMPILER = g++ -ggdb -Wall -pedantic 
CC = $(COMPILER) -I./ -I$(QUEX_PATH) $(NDEBUG_F) -DQUEX_OPTION_ASSERTS

# (*) RULES ____________________________________________________________________
all: copy.exe fill.exe point.exe

# -- char application
          
%.exe: %.cpp $(SOURCES) $(QUEX_CORE)
	$(CC) -o $@ $< tiny_lexer.cpp tiny_lexer-core-engine.cpp 
          
$(SOURCES): simple.qx $(QUEX_CORE)
	quex -i simple.qx --engine tiny_lexer 

# (*) HELPERS __________________________________________________________________
clean:	
	touch simple.qx
	rm -f $(SOURCES)
	rm -f $(WSOURCES)
	rm -f *.o
	rm -f copy fill point
	rm -f *.bak
