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

real-code.cpp: ../count_line_column-with-indentation.i \
               ../count_line_column.i
	./aux/make_code.sh ../count_line_column-with-indentation.i  tmp-x.cpp
	./aux/make_code.sh ../count_line_column.i                   tmp-y.cpp
	cat tmp-x.cpp tmp-y.cpp > real-code.cpp
	rm tmp-x.cpp tmp-y.cpp

test-simple:   real-code.cpp test-simple.cpp
	$(CC) -I./. -I$(QUEX_PATH) $^ -o $@ 
	
test-simple-2: real-code.cpp test-simple-2.cpp
	$(CC) -I./. -I$(QUEX_PATH) $^ -o $@ 
	
clean: 
	rm -f *.o
	rm -f real-code.cpp
	rm -f $(PROGRAMS)

