TESTS := test-FILE.exe \
	     test-POSIX.exe \
	     test-fstream.exe \
	     test-stringstream.exe \
		 segmented-input.exe

FLAGS    :=  -ggdb -Wall -Werror \
   	         -DTEST_FILE_SIZE=100 \
			 -I$(HWUT_PATH)/support/C \
			 -I$(QUEX_PATH) \
			 -I.

all: $(TESTS)

hwut-info:
	@echo $(TESTS)

test-%.exe: test-%.c basic_functionality.c initial_position.c
	gcc $(FLAGS) -D__QUEX_OPTION_PLAIN_C $^ -o $@

test-%.exe: test-%.cpp basic_functionality.c initial_position.c
	g++ $(FLAGS) $^ -o $@

segmented-input.exe: segmented-input.c
	gcc $(FLAGS) -D__QUEX_OPTION_PLAIN_C $^ -o $@

clean:
	rm -f *.exe
	rm -f tmp.*
