# Get: QUEX_CORE dedendencies

TEST_FILES = \
	       BufferFiller_forward_copy.exe \
	       BufferFiller_backward_copy.exe \
	       Buffer_move_forward.exe \
	       Buffer_move_backward.exe \
	       Buffer_tell_and_seek.exe \
	       BufferFiller_forward_copy-32.exe \
	       BufferFiller_backward_copy-32.exe \
	       Buffer_move_forward-32.exe \
	       Buffer_move_backward-32.exe \
	       Buffer_tell_and_seek-32.exe 

DEFS = \
	   -DQUEX_SETTING_BUFFER_MIN_FALLBACK_N=5 \
	   \
	   -D__QUEX_OPTION_UNIT_TEST_QUEX_BUFFER_LOADS \
	   -DQUEX_OPTION_ASSERTS

all: $(TEST_FILES)

hwut-info:
	@echo $(TEST_FILES)

hwut-end: clean
	@echo Bye

%.exe: %.cpp 
	g++ -DQUEX_TYPE_CHARACTER=uint8_t \
		-Wall -Werror \
		-ggdb -I$(QUEX_PATH) $(DEFS) $< -o $@

%.E: %.cpp 
	g++ -E -DQUEX_TYPE_CHARACTER=uint8_t -I$(QUEX_PATH) $(DEFS) $< -o $@

%-32.exe: %.cpp 
	g++ -DQUEX_TYPE_CHARACTER=uint32_t \
		-Wall -Werror \
		-ggdb -I$(QUEX_PATH) $(DEFS) $< -o $@

clean: 
	rm -rf $(TEST_FILES)
