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
CC = @g++ -I./ -I$(QUEX_PATH) $(EXT_CFLAGS) -ggdb

# (*) RULES ____________________________________________________________________
all: error good

# -- application
error: ../lexer-simply.cpp ERROR
	$(CC) $< Simple.cpp -DPRINT_LINE_COLUMN -o $@ 

ERROR:
	@quex -i error.qx -o Simple --token-policy single > tmp.txt 2>&1

good: ../lexer-simply.cpp GOOD
	$(CC) $< Simple.cpp -DPRINT_LINE_COLUMN -o $@ 

GOOD:
	@quex -i good.qx -o Simple --token-policy single --debug-exception > tmp.txt 2>&1


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

