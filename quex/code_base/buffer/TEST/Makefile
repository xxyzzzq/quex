TEST_FILES = \
	       BufferFiller_forward_copy.exe \
	       BufferFiller_forward_pointer_adaption.exe \
	       BufferFiller_backward_copy.exe \
	       BufferFiller_backward_pointer_adaption.exe \

DEFS = \
       -DQUEX_CHARACTER_TYPE=uint8_t \
	   -DQUEX_SETTING_BUFFER_MIN_FALLBACK_N=5 \
	   \
	   -D__QUEX_OPTION_UNIT_TEST_QUEX_BUFFER_LOADS \
	   -DQUEX_OPTION_ASSERTS

all: $(TEST_FILES)

hwut-info:
	@echo $(TEST_FILES)

%.exe: %.cpp
	g++ -I$(QUEX_PATH) $(DEFS) $< -o $@

clean:
	rm -rf $(TEST_FILES)
