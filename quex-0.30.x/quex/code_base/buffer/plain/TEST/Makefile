PROGRAMS = test-forward-get \
	   test-backward-get \
	   # test-forward-get-2 \
	   # test-misc-I test-misc-II \
	   # test-backward-get-2 \
	   # test-misc-III \

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

test-misc-%: test-misc-%.o misc-core.o
	g++ $(INCLUDE_DIRS) $(DEBUGF) $(OPTF) $< misc-core.o -o $@

%.o: %.cpp 
	g++ -c $(INCLUDE_DIRS) $(DEBUGF) $(OPTF) $< -o $@

.cpp: 
	g++ $(INCLUDE_DIRS) $(DEBUGF) $(OPTF) $(FLAGS) $< -o $@

clean:
	rm -f $(PROGRAMS)
	rm -f *.o
