# Get: QUEX_CORE dedendencies
include $(QUEX_PATH)/quex/code_base/core.mkd

TEST_FILES = \
	       strange_stream.exe \
	       strange_wstream.exe \

DEFS = \
	   -DQUEX_OPTION_ASSERTS

all: $(TEST_FILES)

hwut-info:
	@echo $(TEST_FILES)

strange_stream.exe: strange_stream.cpp $(QUEX_CORE)
	g++ -DQUEX_CHARACTER_TYPE=uint8_t \
		-ggdb -I$(QUEX_PATH) $(DEFS) $< -o $@

strange_wstream.exe: strange_wstream.cpp $(QUEX_CORE)
	g++ -DQUEX_CHARACTER_TYPE=wchar_t \
		-ggdb -I$(QUEX_PATH) $(DEFS) $< -o $@


clean: 
	rm -rf $(TEST_FILES)
