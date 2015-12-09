TESTS := $(foreach DIRECTION, backward forward,             \
			 $(foreach FB, 0 1 2, $(DIRECTION)-fb$(FB).exe) \
			 $(DIRECTION)-fb2-32.exe                        \
	     )

FALLBACK_0 := -DQUEX_SETTING_BUFFER_MIN_FALLBACK_N=0 
FALLBACK_1 := -DQUEX_SETTING_BUFFER_MIN_FALLBACK_N=1 
FALLBACK_2 := -DQUEX_SETTING_BUFFER_MIN_FALLBACK_N=2

DEFS = \
	   -D__QUEX_OPTION_PLAIN_C \
	   -DQUEX_OPTION_ASSERTS 

CC_PURE := gcc \
		  -Wall -Werror -ggdb \
		  -I. -I$(QUEX_PATH) -I$(HWUT_PATH)/support/C \
		  $(DEFS) 

CC := gcc \
		  -Wall -Werror -ggdb \
		  -I. -I$(QUEX_PATH) -I$(HWUT_PATH)/support/C \
		  $(DEFS) 

all: $(TESTS)

hwut-info:
	@echo $(TESTS)

hwut-end: clean
	@echo Bye

%-fb0.exe: %.c %-gen.c hwut_cursor.o # basic_functionality.c
	$(CC) $(FALLBACK_0) -DQUEX_TYPE_CHARACTER=uint8_t $^ -o $@ 
%-fb1.exe: %.c %-gen.c hwut_cursor.o # basic_functionality.c
	$(CC) $(FALLBACK_1) -DQUEX_TYPE_CHARACTER=uint8_t $^ -o $@
%-fb2.exe: %.c %-gen.c hwut_cursor.o # basic_functionality.c
	$(CC) $(FALLBACK_2) -DQUEX_TYPE_CHARACTER=uint8_t $^ -o $@
%-fb2-32.exe: %.c %-gen.c hwut_cursor.o # basic_functionality.c
	$(CC) $(FALLBACK_2) -DQUEX_TYPE_CHARACTER=uint32_t $^ -o $@

%-gen.h %-gen.c: %.c
	hwut gen $< -o $(@:.c=)

%.o: %.c %-gen.h
	$(CC) -c $< -o $@

%.o: $(HWUT_PATH)/support/C/%.c 
	$(CC) -c $< -o $@

hwut_cursor.o: $(HWUT_PATH)/support/C/hwut_cursor.c 
	$(CC) -c $< -o $@

clean: 
	rm -rf $(TEST_FILES)
	rm -rf *.o
	rm -rf *-gen.[ch]
	rm -rf *-gen.[ch].[ch]   # some unattended build results ...
	rm -rf *.exe
