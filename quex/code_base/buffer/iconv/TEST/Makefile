include $(QUEX_PATH)/quex/code_base/core.mkd

FILES = \
		one-beat.exe \
		n-beat.exe \
		seek_character_index.exe \
		seek_character_index-zikzak.exe

DEFS = -DQUEX_OPTION_ASSERTS \
	   -DQUEX_SETTING_BUFFER_FILLER_SEEK_TEMP_BUFFER_SIZE=6 \
       -DQUEX_SETTING_BUFFER_MIN_FALLBACK_N=0 

all: $(FILES)

hwut-info:
	@echo $(FILES)

%.exe: %.cpp $(QUEX_CORE)
	g++ -I$(QUEX_PATH) $(DEFS) \
        -DQUEX_CHARACTER_TYPE=uint32_t \
		-ggdb  \
		-D__QUEX_OPTION_UNIT_TEST_INPUT_STRATEGY_ICONV $< -o $@ 

seek_character_index-zikzak.exe: seek_character_index-zikzak.cpp $(QUEX_CORE)
	g++ -I$(QUEX_PATH) $(DEFS) \
		-ggdb  \
		-DQUEX_CHARACTER_TYPE=uint16_t \
		-D__QUEX_OPTION_UNIT_TEST_INPUT_STRATEGY_ICONV $< -o $@

clean:
	rm -f $(FILES)
