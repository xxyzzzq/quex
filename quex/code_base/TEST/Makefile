
TEST_FILES = \
	       strange_stream.exe  \
	       strange_wstream.exe \
		   bom.exe             \
		   bom-istream.exe

DEFS = \
	   -DQUEX_OPTION_ASSERTS

all: $(TEST_FILES)

hwut-info:
	@echo $(TEST_FILES)

bom.exe: bom.c 
	gcc -D__QUEX_OPTION_PLAIN_C \
		-DQUEX_NAMESPACE_MAIN_OPEN="" \
		-DQUEX_NAMESPACE_MAIN_CLOSE="" \
		-I$(HWUT_PATH) \
		-ggdb -I$(QUEX_PATH) $(DEFS) $< -o $@

bom-istream.exe: bom.cpp 
	g++ \
		-DQUEX_NAMESPACE_MAIN_OPEN="" \
		-DQUEX_NAMESPACE_MAIN_CLOSE="" \
		-I$(HWUT_PATH) \
		-ggdb -I$(QUEX_PATH) $(DEFS) $< -o $@

strange_stream.exe: strange_stream.cpp 
	g++ -DQUEX_TYPE_LEXATOM=uint8_t \
		-ggdb -I$(QUEX_PATH) $(DEFS) $< -o $@

strange_wstream.exe: strange_wstream.cpp 
	g++ -DQUEX_TYPE_LEXATOM=wchar_t \
		-ggdb -I$(QUEX_PATH) $(DEFS) $< -o $@


clean: 
	rm -rf $(TEST_FILES)
