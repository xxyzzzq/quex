# PURPOSE: Makefile Demo Application of Quex
#
# ABSOLUTELY NO WARRANTY
#_______________________________________________________________________________
.PHONY: clean

ifndef QUEX_PATH
    $(error The environment variable QUEX_PATH is not defined!)
endif

# (*) SETUP ____________________________________________________________________
# -- INPUT
MODE_FILES       = simple.qx
# -- FILES PRODUCED BY QUEX
ENGINE_NAME      = tiny_lexer# NOTE: a whitespace after this name creates chaos!
ENGINE_SOURCES   = $(ENGINE_NAME)                     \
                   $(ENGINE_NAME).cpp                 \
                   $(ENGINE_NAME)-token_ids           \
		           $(ENGINE_NAME)-core-engine.cpp
# -- OUTPUT
APPLICATION      = lexer

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
	 # -D__QUEX_OPTION_UNIT_TEST \
     # -D__QUEX_OPTION_DEBUG_STATE_TRANSITION_REPORTS \
     # -D__QUEX_OPTION_UNIT_TEST_QUEX_BUFFER_LOADS \
     #-DQUEX_SETTING_BUFFER_SIZE=128

LD = $(COMPILER)

# (*) RULES ____________________________________________________________________
all: $(APPLICATION) 

# -- application
$(APPLICATION): $(APPLICATION).o \
	            $(ENGINE_NAME).o $(ENGINE_NAME)-core-engine.o
	$(LD) ./$(APPLICATION).o $(ENGINE_NAME).o $(ENGINE_NAME)-core-engine.o \
          -o $(APPLICATION) 

# -- engine and object files
%.o: %.cpp $(ENGINE_SOURCES)
	$(CC) $< -o $@

$(ENGINE_SOURCES): $(MODE_FILES)
	@quex -i $(MODE_FILES) --engine $(ENGINE_NAME) --token-queue >& tmp.txt


# (*) HELPERS __________________________________________________________________
clean:	
	@touch $(MODE_FILES)
	@rm -f $(ENGINE_SOURCES)
	@rm -f $(ENGINE_NAME).o
	@rm -f $(ENGINE_NAME)-core-engine.o
	@rm -f lexer.o
	@rm -f lexer
	@rm -f token_ids
	@rm -f *.bak
	@rm -f tmp.txt
	@echo "clean"

