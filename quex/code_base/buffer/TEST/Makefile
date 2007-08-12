PROGRAMS = test-forward-get \
	   test-misc-I test-misc-II test-misc-III \
	   test-backward-get \
	   # test-backward-get-2 \

DEBUGF = -ggdb \
	 -D__QUEX_OPTION_UNIT_TEST \
	 -D__QUEX_OPTION_UNIT_TEST_QUEX_BUFFER 
         # -D__QUEX_OPTION_UNIT_TEST_QUEX_BUFFER_LOADS
INCLUDE_DIRS = -I./ -I$(QUEX_PATH)

OPTF   = # -Os
FLAGS  = #-lefence

all: $(PROGRAMS) 

hwut-info:
	@echo $(PROGRAMS)

test-misc-I: test-misc-I.o misc-core.o
	g++ $(INCLUDE_DIRS) $(DEBUGF) $(OPTF) $< misc-core.o -o $@

test-misc-III: test-misc-III.o misc-core.o
	g++ -I./  -I../../ $(DEBUGF) $(OPTF) $< misc-core.o -o $@

test-misc-II: test-misc-II.o misc-core.o
	g++ $(INCLUDE_DIRS) $(DEBUGF) $(OPTF) $< misc-core.o -o $@

%.o: %.cpp 
	g++ -c $(INCLUDE_DIRS) $(DEBUGF) $(OPTF) $< -o $@

.cpp: 
	g++ $(INCLUDE_DIRS) $(DEBUGF) $(OPTF) $(FLAGS) $< -o $@

clean:
	rm -f $(PROGRAMS)
	rm -f *.o
