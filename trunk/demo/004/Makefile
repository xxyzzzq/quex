# PURPOSE: Makefile Demo Application of Quex
#
# ABSOLUTELY NO WARRANTY
#_______________________________________________________________________________
.PHONY: clean

ifndef QUEX_PATH
    $(error The environment variable QUEX_PATH is not defined!)
endif

# (*) SETUP ____________________________________________________________________
SETUP=-D'EMAIL="fschaef@users.sourceforge.net"' \
      -D'CPU_FREQUENCY_MHZ=((float)(1866.760))' \
      -D'CHARACTER_SIZE=((unsigned)(1))' \
      -D'CPU_NAME="PentiumDuoCore"' \
	  -D'OS="linux-2"' \
	  -D'COMPILER="g++-4.2.1"' \

# -- INPUT
MODE_FILES       = simple.qx
# -- FILES PRODUCED BY QUEX
ENGINE_NAME      = tiny_lexer# NOTE: a whitespace after this name creates chaos!
ENGINE_SOURCES   = $(ENGINE_NAME)                     \
                   $(ENGINE_NAME).cpp                 \
                   $(ENGINE_NAME)-token_ids           \
		           $(ENGINE_NAME)-core-engine.cpp
APPLICATION  = lexer
SOURCE_FILES = lexer.cpp $(ENGINE_NAME).cpp $(ENGINE_NAME)-core-engine.cpp

# (*) COMPILER SETTINGS ________________________________________________________
#     (change COMPILER to whatever you use as compiler on the command line,
#     e.g. "make COMPILER=icpc" will use intel's c++ compiler)
COMPILER = g++
CC = $(COMPILER) -O3 -Wno-deprecated -Wall \
	 -I./ -I$(QUEX_PATH)  \
	 $(SETUP) \
	 -DNDEBUG \
	 -DQUEX_BENCHMARK_SERIOUS \
     #-DQUEX_OPTION_ACTIVATE_ASSERTS	\
     #-DQUEX_SETTING_BUFFER_SIZE=64 \
	 # -D__QUEX_OPTION_UNIT_TEST \
     # -D__QUEX_OPTION_DEBUG_STATE_TRANSITION_REPORTS \
     # -D__QUEX_OPTION_UNIT_TEST_QUEX_BUFFER_LOADS \

LD = $(COMPILER)

# (*) RULES ____________________________________________________________________
#    lexer    --> application w/o line or column counting
#    lexer-l  --> application w/ line counting
#    lexer-lc --> application w/ line and column counting
all: lexer lexer-l lexer-lc

# -- application
lexer-lc: $(SOURCE_FILES)
	$(CC) \
        -DQUEX_OPTION_LINE_NUMBER_COUNTING   \
        -DQUEX_OPTION_COLUMN_NUMBER_COUNTING \
		$(SOURCE_FILES) -o $@

lexer-l: $(SOURCE_FILES)
	$(CC) \
        -DQUEX_OPTION_LINE_NUMBER_COUNTING            \
        -DQUEX_OPTION_COLUMN_NUMBER_COUNTING_DISABLED \
		$(SOURCE_FILES) -o $@

lexer: $(SOURCE_FILES)
	$(CC) \
        -DQUEX_OPTION_LINE_NUMBER_COUNTING_DISABLED \
        -DQUEX_OPTION_COLUMN_NUMBER_COUNTING_DISABLED \
		$(SOURCE_FILES) -o $@


$(ENGINE_SOURCES): $(MODE_FILES)
	quex -i $(MODE_FILES) --engine $(ENGINE_NAME) --token-offset 3 

# (*) HELPERS __________________________________________________________________
clean:	
	rm -f lexer lexer-l lexer-lc
	touch $(MODE_FILES)
	rm -f $(ENGINE_SOURCES)
	rm -f $(ENGINE_NAME).o
	rm -f $(ENGINE_NAME)-core-engine.o
	rm -f lexer.o
	rm -f lexer
	rm -f token_ids
	rm -f *.bak
	rm -f extensive-example.txt

