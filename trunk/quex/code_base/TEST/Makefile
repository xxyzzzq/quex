# Get: QUEX_CORE dedendencies
include $(QUEX_PATH)/quex/code_base/core.mkd

TEST_FILES = \
	       strange_stream.exe \
	       strange_wstream.exe \
		   bom.exe

DEFS = \
	   -DQUEX_OPTION_ASSERTS

all: $(TEST_FILES)

hwut-info:
	@echo $(TEST_FILES)

bom.exe: bom.c $(QUEX_CORE)
	gcc -D__QUEX_OPTION_PLAIN_C \
		-DQUEX_NAMESPACE_MAIN_OPEN="" \
		-DQUEX_NAMESPACE_MAIN_CLOSE="" \
		-ggdb -I$(QUEX_PATH) $(DEFS) $< -o $@

strange_stream.exe: strange_stream.cpp $(QUEX_CORE)
	g++ -DQUEX_TYPE_CHARACTER=uint8_t \
		-ggdb -I$(QUEX_PATH) $(DEFS) $< -o $@

strange_wstream.exe: strange_wstream.cpp $(QUEX_CORE)
	g++ -DQUEX_TYPE_CHARACTER=wchar_t \
		-ggdb -I$(QUEX_PATH) $(DEFS) $< -o $@


clean: 
	rm -rf $(TEST_FILES)
