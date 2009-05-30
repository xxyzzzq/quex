# PURPOSE: Makefile Demo Application of Quex
#
# ABSOLUTELY NO WARRANTY
#_______________________________________________________________________________
.PHONY: clean

FILES = copy.exe    fill.exe    point.exe \
		copy-ez.exe fill-ez.exe

ifndef QUEX_PATH
    $(error The environment variable QUEX_PATH is not defined!)
endif

include $(QUEX_PATH)/quex/code_base/core.mkd

# (*) SETUP ____________________________________________________________________
SOURCES  = tiny_lexer.cpp tiny_lexer-core-engine.cpp

# (*) COMPILER SETTINGS ________________________________________________________
#     (change COMPILER to whatever you use as compiler on the command line,
#      e.g. "make COMPILER=icpc" will use intel's c++ compiler)
COMPILER = g++ -ggdb -Wall -pedantic -DQUEX_TYPE_CHARACTER=uint8_t
CC = $(COMPILER) -I./ -I$(QUEX_PATH) $(NDEBUG_F) -DQUEX_OPTION_ASSERTS

# (*) RULES ____________________________________________________________________
all: $(FILES)

# -- char application
          
%.exe: %.cpp $(SOURCES:.cpp=.o) $(QUEX_CORE) messaging-framework.o
	$(CC) -o $@ $< tiny_lexer.o tiny_lexer-core-engine.o messaging-framework.o
          
$(SOURCES): simple.qx $(QUEX_CORE)
	quex -i simple.qx --engine tiny_lexer --token-policy users_token

%.o: %.cpp $(QUEX_CORE)
	$(CC) -c $< -o $@  
          
# (*) HELPERS __________________________________________________________________
clean:	
	touch simple.qx
	rm -f tiny_lexer*
	rm -f $(SOURCES)
	rm -f $(FILES)
	rm -f *.o
	rm -f copy fill point
	rm -f *.bak
