# Get: QUEX_CORE dedendencies
include $(QUEX_PATH)/quex/code_base/core.mkd

PROGRAMS = \
		   post-categorizer-enter.exe \
		   post-categorizer-remove.exe \
		   post-categorizer-remove-2.exe \
		   post-categorizer-remove-total.exe \
		   post-categorizer-find.exe \
		   accumulator.exe \
	       statistics.exe

all:       $(PROGRAMS) 

.PHONY: hwut-info
hwut-info: 
	@echo $(PROGRAMS)

MYFLAGS = \
     -ggdb \
	 -Wall -Werror \
	 -I$(QUEX_PATH) \
     -DQUEX_OPTION_LINE_NUMBER_COUNTING  \
     -DQUEX_OPTION_COLUMN_NUMBER_COUNTING 

CC = g++ $(MYFLAGS)

post-categorizer-%.exe:   post-categorizer-%.cpp $(QUEX_CORE)
	$(CC) -I./. $< post-categorizer-common.cpp -o $@ 
	
counter-%.exe:   counter-%.cpp $(QUEX_CORE)
	$(CC) -I./. $< -o $@ 

accumulator.exe: accumulator.cpp $(QUEX_CORE)
	$(CC) -I./. $< -o $@ 

nonsense.exe: nonsense.cpp $(QUEX_CORE)
	$(CC) -I./. $< -o $@ 

statistics.exe: statistics.c $(QUEX_CORE)
	gcc $(MYFLAGS) -I./. -I$(HWUT_PATH) $< -o $@ \
		-D__QUEX_OPTION_PLAIN_C

%.E:   %.cpp $(QUEX_CORE)
	$(CC) -E -I./. $< -o $@ 

clean: 
	rm -f *.o
	rm -f *.E
	rm -f $(PROGRAMS)

