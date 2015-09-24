# Get: QUEX_CORE dedendencies

TEST_FILES = \
	       Buffer_seek_forward-8.exe   \
	       Buffer_seek_forward-32.exe  \
	       Buffer_seek_backward-8.exe  \
	       Buffer_seek_backward-32.exe \
	       Buffer_tell_and_seek-8.exe  \
	       Buffer_tell_and_seek-32.exe 

DEFS = \
	   -D__QUEX_OPTION_UNIT_TEST_QUEX_BUFFER_LOADS \
	   -DQUEX_OPTION_ASSERTS

CC := g++ -Wall -Werror -ggdb \
	      -DQUEX_SETTING_BUFFER_MIN_FALLBACK_N=5 \
		  -I. -I$(QUEX_PATH) -I$(HWUT_PATH)/support/C \
		  $(DEFS) 

all: $(TEST_FILES)

hwut-info:
	@echo $(TEST_FILES)

hwut-end: clean
	@echo Bye

hwut_cursor.o: $(HWUT_PATH)/support/C/hwut_cursor.c 
	$(CC) -c $< -o $@

%-8.exe: %.cpp 
	$(CC) -DQUEX_TYPE_CHARACTER=uint8_t \
		-Wall -Werror \
		-ggdb -I. -I$(QUEX_PATH) -I$(HWUT_PATH)/support/C \
		$< -o $@

%-32.exe: %.cpp 
	$(CC) -DQUEX_TYPE_CHARACTER=uint32_t \
		-Wall -Werror \
		-ggdb -I. -I$(QUEX_PATH) -I$(HWUT_PATH)/support/C \
		$(DEFS) $< -o $@

%.E: %.cpp 
	$(CC) -E -DQUEX_TYPE_CHARACTER=uint8_t \
		-I$(HWUT_PATH)/support/C -I$(QUEX_PATH) \
		$(DEFS) $< -o $@

%-gen.c: %.cpp
	hwut gen $< -o $(@:.c=)

%.o: %.c
	$(CC) -c $< -o $@

clean: 
	rm -rf $(TEST_FILES)
	rm -rf *.o
	rm -rf *-gen.[ch]
	rm -rf *.exe
