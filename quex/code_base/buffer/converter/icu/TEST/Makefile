# include $(QUEX_PATH)/quex/code_base/core.mkd

FILES = \
		converter-16.exe \
		converter-32.exe \
		converter-statefulness-16.exe \
		converter-statefulness-32.exe \
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

CC = \
	g++ -I$(QUEX_PATH) $(DEFS) \
		-ggdb  \
		-Wall \
		$(ICU_FLAGS) \
		-DQUEX_OPTION_ENABLE_ICU

hwut-info:
	@echo $(FILES)

%.exe: %.cpp $(QUEX_CORE)
	$(CC) $< -o $@ \
        -DQUEX_TYPE_CHARACTER=uint32_t 

%-16.exe: %.cpp $(QUEX_CORE)
	$(CC) $< -o $@ \
        -DQUEX_TYPE_CHARACTER=uint16_t 

%-32.exe: %.cpp $(QUEX_CORE)
	$(CC) $< -o $@ \
        -DQUEX_TYPE_CHARACTER=uint32_t 

seek_character_index-zikzak.exe: seek_character_index-zikzak.cpp $(QUEX_CORE)
	$(CC) $< -o $@ \
		-DQUEX_TYPE_CHARACTER=uint16_t 

clean:
	rm -f $(FILES)
