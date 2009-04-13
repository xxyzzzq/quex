# Get: QUEX_CORE dedendencies
include $(QUEX_PATH)/quex/code_base/core.mkd

PROGRAMS = counter-column_line.exe \
		   counter-column_line-x.exe \
		   counter-column_line-indentation.exe \
		   counter-column_line-indentation-x.exe \
		   post-categorizer-enter.exe \
		   post-categorizer-delete.exe \
		   post-categorizer-delete-2.exe \
		   post-categorizer-find.exe

all:       $(PROGRAMS) 

.PHONY: hwut-info
hwut-info: 
	@echo $(PROGRAMS)

CC = g++ \
     -ggdb \
	 -Wall \
     -DQUEX_OPTION_LINE_NUMBER_COUNTING  \
     -DQUEX_OPTION_COLUMN_NUMBER_COUNTING \
     -D__QUEX_OPTION_INDENTATION_TRIGGER_SUPPORT 

%.exe:   %.cpp $(QUEX_CORE)
	$(CC) -I./. -I$(QUEX_PATH) $< post-categorizer-common.cpp -o $@ 
	
clean: 
	rm -f *.o
	rm -f $(PROGRAMS)

