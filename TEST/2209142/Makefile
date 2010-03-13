# PURPOSE: Makefile Demo Application of Quex
#
# ABSOLUTELY NO WARRANTY
#_______________________________________________________________________________
.PHONY: clean ERROR GOOD

ifndef QUEX_PATH
    $(error The environment variable QUEX_PATH is not defined!)
endif

# (*) SETUP ____________________________________________________________________
# -- INPUT
# -- FILES PRODUCED BY QUEX
#
# (*) COMPILER SETTINGS ________________________________________________________
CC = g++ -I./ -I$(QUEX_PATH) $(EXT_CFLAGS) -ggdb

# (*) RULES ____________________________________________________________________
all: error good

# -- application
error: ../lexer.cpp ERROR
	$(CC) $< Simple.cpp -o $@ 

ERROR:
	@quex -i error.qx --engine Simple --token-policy single >& tmp.txt

good: lexer.cpp GOOD
	$(CC) $< Simple.cpp -o $@ 

GOOD:
	@quex -i good.qx --engine Simple --token-policy single >& tmp.txt


# (*) HELPERS __________________________________________________________________
clean:	
	@rm -f $(ENGINE_SOURCES)
	@rm -f Simple*
	@rm -f lexer.o
	@rm -f lexer
	@rm -f *.bak
	@rm -f tmp.txt
	@rm -f good error
	@echo "clean"

