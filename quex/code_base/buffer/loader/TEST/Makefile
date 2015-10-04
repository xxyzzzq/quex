TESTS := test-FILE.exe

CC    := gcc -ggdb -Wall -Werror \
   	         -DTEST_FILE_SIZE=100 \
			 -D__QUEX_OPTION_PLAIN_C \
			 -I$(HWUT_PATH)/support/C \
			 -I$(QUEX_PATH) \
			 -I.

all: $(TESTS)

hwut-info:
	@echo $(TESTS)

test-%.exe: test-%.c basic_functionality.c
	$(CC) $^ -o $@
