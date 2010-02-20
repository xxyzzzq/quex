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
# -- INPUT
MODE_FILES       = simple.qx
# -- FILES PRODUCED BY QUEX
ENGINE_NAME      = tiny_lexer# NOTE: a whitespace after this name creates chaos!
ENGINE_SOURCES   = $(ENGINE_NAME)                     \
                   $(ENGINE_NAME).cpp                 \
                   $(ENGINE_NAME)-token_ids           \
                   $(ENGINE_NAME)-configuration     

# (*) COMPILER SETTINGS ________________________________________________________
#     (change COMPILER to whatever you use as compiler on the command line,
#      e.g. "make COMPILER=icpc" will use intel's c++ compiler)
COMPILER = g++ -std=c++0x -Wconversion -ggdb -Wall -pedantic -DQUEX_OPTION_NO_COMPUTED_GOTOS
CC = $(COMPILER) -c \
	 -I./ -I$(QUEX_PATH) $(NDEBUG_F) \
     -DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED 

LD = $(COMPILER) 

# (*) RULES ____________________________________________________________________
# -- application
lexer: example.o $(ENGINE_NAME).o 
	$(LD) -o $@ example.o $(ENGINE_NAME).o 
          

# -- engine and object files
%.o: ../%.cpp $(ENGINE_SOURCES)
	$(CC) $< -o $@ # -D__QUEX_OPTION_DEBUG_STATE_TRANSITION_REPORTS

%.o: %.cpp $(ENGINE_SOURCES)
	$(CC) $< -o $@ # -D__QUEX_OPTION_DEBUG_STATE_TRANSITION_REPORTS

%.E: %.cpp $(ENGINE_SOURCES)
	$(CC) -E $< -o $@ 


$(ENGINE_SOURCES): $(MODE_FILES) $(QUEX_CORE)
	quex -i $(MODE_FILES) --engine $(ENGINE_NAME) --token-offset 0x1000 \
		 --post-categorizer

# (*) HELPERS __________________________________________________________________
clean:	
	touch $(MODE_FILES)
	rm -f $(ENGINE_SOURCES)
	rm -f $(ENGINE_NAME).o
	rm -f $(ENGINE_NAME)-token
	rm -f lexer.o
	rm -f lexer
	rm -f token_ids
	rm -f *.bak
	rm -f *.E
