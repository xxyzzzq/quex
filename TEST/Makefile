TEST_FILES = bug-1935701.exe


DEBUGF = -ggdb \
         -D__QUEX_OPTION_UNIT_TEST \
         -D__QUEX_OPTION_UNIT_TEST_QUEX_BUFFER \

INCLUDE_DIRS = -I./ -I$(QUEX_PATH)

OPTF   = # -Os
FLAGS  = #-lefence

all: $(TEST_FILES) 

hwut-info:
	@echo $(TEST_FILES) 

%.exe: %.cpp  
	g++ -Wall -Werror -DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED $(INCLUDE_DIRS) $(DEBUGF) $(OPTF) $< -o $@

clean:
	rm -f $(TEST_FILES)
	rm -f *.o
