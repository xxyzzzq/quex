# PURPOSE: Makefile Demo Application of Quex
#
# ABSOLUTELY NO WARRANTY
#_______________________________________________________________________________
.PHONY: clean

ifndef QUEX_PATH
    $(error The environment variable QUEX_PATH is not defined!)
endif

# (*) COMPILER SETTINGS ________________________________________________________
#     (change COMPILER to whatever you use as compiler on the command line,
#     e.g. "make COMPILER=icpc" will use intel's c++ compiler)
#     
#     Buffer sizes:   28 --> buffer overflow
#                     29 --> OK
COMPILER = g++
CC = $(COMPILER) -c -fPIC -Wno-deprecated -Wall \
	 -I./ -I$(QUEX_PATH) $(NDEBUG_F) \
     -DQUEX_SETTING_BUFFER_SIZE=$(BUFFER_SIZE) \
	 -DQUEX_OPTION_ACTIVATE_ASSERTS \
	 -DTEST_EPILOG='std::printf("Buffer Size = %i\n", QUEX_SETTING_BUFFER_SIZE);'
	 # -D__QUEX_OPTION_UNIT_TEST \
     # -DQUEX_OPTION_DEBUG_SHOW \
     # -D__QUEX_OPTION_UNIT_TEST_QUEX_BUFFER_LOADS \

LD = $(COMPILER)

# (*) RULES ____________________________________________________________________
all: lexer

# -- application
lexer: lexer.o Simple.o 
	$(LD) lexer.o Simple.o -o $@

# -- engine and object files
lexer.o: ../lexer.cpp Simple.cpp
	$(CC) -Wall $< -ggdb -o $@

%.o: %.cpp Simple.cpp
	$(CC) -Wall $< -ggdb -o $@

Simple.cpp: simple.qx
	@quex -i simple.qx --engine Simple --debug-exception > tmp.txt 2>&1

# (*) HELPERS __________________________________________________________________
mostlyclean:
	@rm -f Simple.o
	@rm -f lexer.o
	@rm -f lexer
	@rm -f *.bak
	@rm -f tmp.txt
	@echo "clean"

clean:	
	@touch simple.qx
	@rm -f Simple*
	@rm -f Simple.o
	@rm -f lexer.o
	@rm -f lexer
	@rm -f token_ids
	@rm -f *.bak
	@rm -f tmp.txt
	@echo "clean"

