# include $(QUEX_PATH)/quex/code_base/core.mkd

FILES = \
		converter-16.exe

OUT_FILES = \
		one-beat.exe \
		n-beat.exe \
		seek_character_index.exe \
		seek_character_index-zikzak.exe \
		Buffer_move_forward.exe \
		Buffer_tell_and_seek.exe \
		Buffer_move_backward.exe

DEFS = -DQUEX_OPTION_ASSERTS \
	   -DQUEX_SETTING_BUFFER_FILLER_SEEK_TEMP_BUFFER_SIZE=6 \
       -DQUEX_SETTING_BUFFER_MIN_FALLBACK_N=0 \

# Use 'icu-config --ldflags' in order to get the linker flags
ICU_FLAGS = \
		   -lpthread -lm -L/usr/lib -licui18n -licuuc -licudata -lpthread -lm

all: $(FILES)

hwut-info:
	@echo $(FILES)

%-16.exe: %.cpp $(QUEX_CORE)
	g++ -I$(QUEX_PATH) $(DEFS) \
        -DQUEX_CHARACTER_TYPE=uint16_t \
		-ggdb  \
		-Wall \
		$(ICU_FLAGS) \
		-D__QUEX_OPTION_UNIT_TEST_INPUT_STRATEGY_ICU $< -o $@ 

seek_character_index-zikzak.exe: seek_character_index-zikzak.cpp $(QUEX_CORE)
	g++ -I$(QUEX_PATH) $(DEFS) \
		-ggdb  \
		-Wall \
		-DQUEX_CHARACTER_TYPE=uint16_t \
		-D__QUEX_OPTION_UNIT_TEST_INPUT_STRATEGY_ICU $< -o $@

clean:
	rm -f $(FILES)
