FILES = \
		one-beat.exe \
		n-beat.exe \
		seek_character_index.exe \
		seek_character_index-zikzak.exe

DEFS = -DQUEX_OPTION_ASSERTS \
	   -DQUEX_SETTING_BUFFER_FILLER_SEEK_TEMP_BUFFER_SIZE=6 \
       -DQUEX_SETTING_BUFFER_MIN_FALLBACK_N=0 

HEADERS = \
		  $(QUEX_PATH)/quex/code_base/buffer/iconv/BufferFiller_IConv      \
		  $(QUEX_PATH)/quex/code_base/definitions                          \
		  $(QUEX_PATH)/quex/code_base/asserts                              \
		  $(QUEX_PATH)/quex/code_base/temporary_macros_on                  \
		  $(QUEX_PATH)/quex/code_base/temporary_macros_off                 \
		  $(QUEX_PATH)/quex/code_base/buffer/iconv/BufferFiller_IConv.i    \
		  $(QUEX_PATH)/quex/code_base/buffer/BufferFiller.i                \
		  $(QUEX_PATH)/quex/code_base/buffer/Buffer.i                      \
		  $(QUEX_PATH)/quex/code_base/buffer/Buffer_debug.i                \
		  $(QUEX_PATH)/quex/code_base/buffer/plain/BufferFiller_Plain      \
		  $(QUEX_PATH)/quex/code_base/buffer/InputPolicy                   \
		  $(QUEX_PATH)/quex/code_base/buffer/Buffer                        \
		  $(QUEX_PATH)/quex/code_base/buffer/BufferFiller                  \
		  $(QUEX_PATH)/quex/code_base/compatibility/inttypes.h             \
		  $(QUEX_PATH)/quex/code_base/compatibility/pseudo-stdbool.h       \
		  $(QUEX_PATH)/quex/code_base/compatibility/iconv-argument-types.h

all: $(FILES)

hwut-info:
	@echo $(FILES)

%.exe: %.cpp $(HEADERS)
	g++ -I$(QUEX_PATH) $(DEFS) \
        -DQUEX_CHARACTER_TYPE=uint32_t \
		-ggdb  \
		-D__QUEX_OPTION_UNIT_TEST_INPUT_STRATEGY_ICONV $< -o $@ 

seek_character_index-zikzak.exe: seek_character_index-zikzak.cpp $(HEADERS)
	g++ -I$(QUEX_PATH) $(DEFS) \
		-ggdb  \
		-DQUEX_CHARACTER_TYPE=uint16_t \
		-D__QUEX_OPTION_UNIT_TEST_INPUT_STRATEGY_ICONV $< -o $@

clean:
	rm -f $(FILES)
