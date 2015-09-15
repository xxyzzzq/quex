# Get: QUEX_CORE dedendencies

TEST_FILES = \
	       BufferFiller_forward_copy.exe \
	       BufferFiller_forward_copy-32.exe \
	       BufferFiller_backward_copy.exe \
	       BufferFiller_backward_copy-32.exe \
	       Buffer_move_forward.exe \
	       Buffer_move_backward.exe \
	       Buffer_tell_and_seek.exe \
	       Buffer_move_forward-32.exe \
	       Buffer_move_backward-32.exe \
	       Buffer_tell_and_seek-32.exe 

DEFS = \
	   \
	   -D__QUEX_OPTION_UNIT_TEST_QUEX_BUFFER_LOADS \
	   -DQUEX_OPTION_ASSERTS

CC := g++ -DQUEX_TYPE_CHARACTER=uint8_t \
		  -Wall -Werror -ggdb \
		  -I. -I$(QUEX_PATH) -I$(HWUT_PATH)/support/C \
		  $(DEFS) 

all: $(TEST_FILES)

hwut-info:
	@echo $(TEST_FILES)

hwut-end: clean
	@echo Bye

%-gen.c: %.cpp
	hwut gen $< -o $(@:.c=)

move_away_passed_content.exe: move_away_passed_content.cpp \
	                          move_away_passed_content-gen.o \
							  hwut_cursor.o
	$(CC) $< -DQUEX_SETTING_BUFFER_MIN_FALLBACK_N=2 \
		  move_away_passed_content-gen.o hwut_cursor.o -o $@
	   

%.o: %.c
	$(CC) -c $< -o $@

hwut_cursor.o: $(HWUT_PATH)/support/C/hwut_cursor.c 
	$(CC) -c $< -o $@

%.exe: %.cpp MOPC-gen.h
	g++ -DQUEX_TYPE_CHARACTER=uint32_t \
		-Wall -Werror \
		-ggdb -I. -I$(QUEX_PATH) -I$(HWUT_PATH)/support/C \
		$< -o $@

%.E: %.cpp 
	g++ -E -DQUEX_TYPE_CHARACTER=uint8_t -I$(HWUT_PATH)/support/C -I$(QUEX_PATH) $(DEFS) $< -o $@

%-32.exe: %.cpp 
	g++ -DQUEX_TYPE_CHARACTER=uint32_t \
		-Wall -Werror \
		-ggdb -I. -I$(QUEX_PATH) -I$(HWUT_PATH)/support/C \
		$(DEFS) $< -o $@

clean: 
	rm -rf $(TEST_FILES)
	rm -rf *.o
	rm -rf *-gen.[ch]
