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
# -- FILES PRODUCED BY QUEX
ENGINE_NAME    = Simple# NOTE: a whitespace after this name creates chaos!
ENGINE_SOURCES = $(ENGINE_NAME)                     \
                 $(ENGINE_NAME).cpp                 \
                 $(ENGINE_NAME)-token_ids           \
                 $(ENGINE_NAME)-configuration       \
                 $(ENGINE_NAME)-token               \

# (*) COMPILER SETTINGS ________________________________________________________
CC = @g++ -I./ -I$(QUEX_PATH) $(EXT_CFLAGS) -ggdb \
	 -DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED

# (*) RULES ____________________________________________________________________
all: lexer

# -- application
lexer: ../lexer-simply.cpp $(ENGINE_SOURCES)
	$(CC) $< $(ENGINE_NAME).cpp -o $@ 

Simple.E: Simple.cpp
	$(CC) -E $< -o $@ 

$(ENGINE_SOURCES): $(EXT_MODE_FILE)
	@quex -i $(EXT_MODE_FILE) --engine $(ENGINE_NAME) $(EXT_TOKEN_QUEUE_FLAG) >& tmp.txt


# (*) HELPERS __________________________________________________________________
clean:	
	@rm -f $(ENGINE_SOURCES)
	@rm -f $(ENGINE_NAME).o
	@rm -f lexer.o
	@rm -f lexer
	@rm -f token_ids
	@rm -f *.bak
	@rm -f tmp.txt

