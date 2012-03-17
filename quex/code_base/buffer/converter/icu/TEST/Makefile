.SECONDARY: $(GENERATED_FILES)

include $(QUEX_PATH)/quex/code_base/core.mkd

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

GENERATED_FILES = \
				  Buffer_tell_and_seek.cpp \
		          Buffer_move_forward.cpp  \
		          Buffer_move_backward.cpp \
				  converter.cpp            \
				  converter-statefulness.cpp      \
		          seek_character_index-zikzak.cpp 

DEFS = -DQUEX_OPTION_ASSERTS \
	   -DQUEX_SETTING_BUFFER_FILLER_SEEK_TEMP_BUFFER_SIZE=6 \
       -DQUEX_SETTING_BUFFER_MIN_FALLBACK_N=0 \

# Use 'icu-config --ldflags' in order to get the linker flags
ICU_FLAGS := $(shell icu-config --ldflags) 
CFLAGS    := $(shell icu-config --cppflags) 

all: $(FILES)

CC = \
	g++ -I$(QUEX_PATH) $(DEFS) \
		-ggdb  \
		-Wall \
        -Werror-implicit-function-declaration \
		$(ICU_FLAGS) \
		-DQUEX_OPTION_CONVERTER_ICU

HEADER        = \<quex\/code_base\/buffer\/converter\/icu\/Converter_ICU\.i\>
CONVERTER     = QUEX_NAME(Converter_ICU_convert)
NEW_OPERATOR  = QUEX_NAME(Converter_ICU_new)
CODING_4_BYTE = "UTF-32BE"


hwut-info:
	@echo $(FILES)

hwut-end: clean
	@echo Bye


%.cpp: ../../iconv/TEST/%-template.cpp
	sed   -e 's/\_\_\_HEADER\_\_\_/$(HEADER)/g' $<    \
	| sed -e 's/\_\_\_NEW\_\_\_/$(NEW_OPERATOR)/g'    \
	| sed -e 's/\_\_\_CONVERT\_\_\_/$(CONVERTER)/g' \
	| sed -e 's/\_\_\_CODING_4_BYTE\_\_\_/$(CODING_4_BYTE)/g' \
	> $@

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
	rm -f $(GENERATED_FILES)
