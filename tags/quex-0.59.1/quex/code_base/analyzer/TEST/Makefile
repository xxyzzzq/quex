# Get: QUEX_CORE dedendencies
include $(QUEX_PATH)/quex/code_base/core.mkd

PROGRAMS = counter-column_line.exe \
		   counter-column_line-x.exe \
		   post-categorizer-enter.exe \
		   post-categorizer-remove.exe \
		   post-categorizer-remove-2.exe \
		   post-categorizer-remove-total.exe \
		   post-categorizer-find.exe \
		   accumulator.exe

all:       $(PROGRAMS) 

.PHONY: hwut-info
hwut-info: 
	@echo $(PROGRAMS)

CC = g++ \
     -ggdb \
	 -Wall \
     -DQUEX_OPTION_LINE_NUMBER_COUNTING  \
     -DQUEX_OPTION_COLUMN_NUMBER_COUNTING 

post-categorizer-%.exe:   post-categorizer-%.cpp $(QUEX_CORE)
	$(CC) -I./. -I$(QUEX_PATH) $< post-categorizer-common.cpp -o $@ 
	
counter-%.exe:   counter-%.cpp $(QUEX_CORE)
	$(CC) -I./. -I$(QUEX_PATH) $< -o $@ 

accumulator.exe: accumulator.cpp $(QUEX_CORE)
	$(CC) -I./. -I$(QUEX_PATH) $< -o $@ 

nonsense.exe: nonsense.cpp $(QUEX_CORE)
	$(CC) -I./. -I$(QUEX_PATH) $< -o $@ 


%.E:   %.cpp $(QUEX_CORE)
	$(CC) -E -I./. -I$(QUEX_PATH) $< -o $@ 

clean: 
	rm -f *.o
	rm -f *.E
	rm -f $(PROGRAMS)

