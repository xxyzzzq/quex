# PURPOSE: Makefile Demo Application of Quex
#
# ABSOLUTELY NO WARRANTY
#_______________________________________________________________________________
APPLICATION_LIST = bug_xyz \

.PHONY: clean $(addsuffix -sources, $(APPLICATION_LIST))

ifndef QUEX_PATH
    $(error The environment variable QUEX_PATH is not defined!)
endif

# (*) SETUP ____________________________________________________________________
# -- FILES PRODUCED BY QUEX
ENGINE_NAME      = anti_bug# NOTE: a whitespace after this name creates chaos!
ENGINE_SOURCES   = \
				   tester                     \
                   tester.cpp                 \
                   tester-token_ids           \
		           tester-core-engine.cpp
ENGINE_OBJS      = \
                   tester.o                   \
		           tester-core-engine.o


# (*) COMPILER SETTINGS ________________________________________________________
# (change g++ to whatever you use as compiler)
CC = @g++ -c -fPIC -Wno-deprecated -Wall -I./ -I$(QUEX_PATH) 

LD = @g++ -ggdb 

# (*) RULES ____________________________________________________________________
# -- application
bug_%: bug_%/lexer.o $(addprefix bug_%/, $(ENGINE_OBJS))
	$(LD) $< $(addprefix bug_%/, $(ENGINE_OBJS)) -o $@ 
	@echo "[LD] $@"

bug_%/lexer.cpp: 
	@chmod u+x ./adapt-lexer.sh
	@./adapt-lexer.sh $(dir $@) 
	@echo "[--] $@"

# -- engine and object files
bug_%/lexer.o: bug_%/lexer.cpp
	$(CC) $< -o $@
	@echo "[CC] $@"

bug_%/tester.o: bug_%/tester.cpp %-sources
	$(CC) $< -o $@
	@echo "[CC] $@"

bug_%/tester-core-engine.o: bug_%/tester-core-engine.cpp %-sources
	$(CC) $< -o $@
	@echo "[CC] $@"

bug_%-sources: $(addprefix bug_%, $(ENGINE_SOURCES))
	@quex -i $(subst -source,,$@))/description.qx --engine $(ENGINE_NAME)
	@echo "[QX] $@"

# (*) HELPERS __________________________________________________________________
clean:	
	touch $(MODE_FILES)
	rm -f $(ENGINE_SOURCES)
	rm -f $(BUG_ID).o
	rm -f $(BUG_ID)-core-engine.o
	rm -f lexer.o
	rm -f lexer
	rm -f token_ids
	rm -f *.bak
