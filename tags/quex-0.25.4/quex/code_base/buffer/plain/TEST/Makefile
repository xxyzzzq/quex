PROGRAMS = test-forward-get \
	   test-forward-get-2 \
	   test-misc-I test-misc-II test-misc-III \
	   test-backward-get \
	   # test-backward-get-2 \

DEBUGF = -ggdb \
	 -D__QUEX_OPTION_UNIT_TEST \
	 -DQUEX_OPTION_ACTIVATE_ASSERTS \
     # -D__QUEX_OPTION_UNIT_TEST_QUEX_BUFFER_LOADS

INCLUDE_DIRS = -I./ -I$(QUEX_PATH) -I../

OPTF   = -ggdb # -Os
FLAGS  = #-lefence

all: $(PROGRAMS) 

hwut-info:
	@echo $(PROGRAMS)

nice-try:
ifdef all
endif
ifdef test-backward-get
	@echo Backward Iteration: Multiple Loads;
	@echo CHOICES: BLC=0, BLC=1, BLC=0xFF;
	@echo SAME;
endif
ifdef test-backward-get-2
	@echo Backward Iteration: EOF at first load;
endif
ifdef test-forward-get
	@echo Forward Iteration: Multiple Loads;
	@echo CHOICES: BLC=0, BLC=1, BLC=0xFF;
	@echo SAME;
endif
ifdef test-forward-get-2
	@echo Forward Iteration: EOF at first load;
endif
ifdef test-misc-I
	@echo Miscenllaneous Scenarios: Content Size = 11, Fallback Size = 10;
	@echo CHOICES: istream, stdio;
	@echo SAME;
endif
ifdef test-misc-II
	@echo Miscenllaneous Scenarios: Content Size = 11, Fallback Size = 1;
	@echo CHOICES: istream, stdio;
	@echo SAME;
endif
ifdef test-misc-III
	@echo Miscenllaneous Scenarios: Content Size = 11, Fallback Size = 0;
	@echo CHOICES: istream, stdio;
	@echo SAME;
endif

test-misc-%: test-misc-%.o misc-core.o
	g++ $(INCLUDE_DIRS) $(DEBUGF) $(OPTF) $< misc-core.o -o $@

%.o: %.cpp 
	g++ -c $(INCLUDE_DIRS) $(DEBUGF) $(OPTF) $< -o $@

.cpp: 
	g++ $(INCLUDE_DIRS) $(DEBUGF) $(OPTF) $(FLAGS) $< -o $@

clean:
	rm -f $(PROGRAMS)
	rm -f *.o
