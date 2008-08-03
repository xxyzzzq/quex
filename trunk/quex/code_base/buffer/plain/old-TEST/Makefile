TEST_FILES = \
	       BufferFiller_forward_load-1.exe \
	       BufferFiller_forward_load-2.exe \
	       BufferFiller_forward_load-4.exe \
	       BufferFiller_backward_load.exe

DEFS = \
	   -DQUEX_SETTING_BUFFER_MIN_FALLBACK_N=2 \
	   \
	   -DQUEX_OPTION_ASSERTS

all: $(TEST_FILES)

hwut-info:
	@echo $(TEST_FILES)

%-4.exe: %.cpp
	g++ -ggdb -DQUEX_CHARACTER_TYPE=uint32_t -I$(QUEX_PATH) $(DEFS) $< -o $@

%-2.exe: %.cpp
	g++ -ggdb -DQUEX_CHARACTER_TYPE=uint16_t -I$(QUEX_PATH) $(DEFS) $< -o $@

%-1.exe: %.cpp
	g++ -ggdb -DQUEX_CHARACTER_TYPE=uint8_t  -I$(QUEX_PATH) $(DEFS) $< -o $@

clean:
	rm -rf $(TEST_FILES)
