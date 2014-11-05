PROGRAMS = test-simple test-simple-2

all:       $(PROGRAMS) 

.PHONY: hwut-info
hwut-info: 
	@echo $(PROGRAMS)

CC = g++ \
     -ggdb \
     -DQUEX_OPTION_LINE_NUMBER_COUNTING  \
     -DQUEX_OPTION_COLUMN_NUMBER_COUNTING \
     -D__QUEX_OPTION_INDENTATION_TRIGGER_SUPPORT 

test-simple:   test-simple.cpp
	$(CC) -I./. -I$(QUEX_PATH) $^ -o $@ 
	
test-simple-2: test-simple-2.cpp
	$(CC) -I./. -I$(QUEX_PATH) $^ -o $@ 
	
clean: 
	rm -f *.o
	rm -f real-code.cpp
	rm -f $(PROGRAMS)

