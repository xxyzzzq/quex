.SECONDARY: $(GENERATED_FILES)


FILES = \
		converter-16.exe                \
		converter-32.exe                \
		converter-statefulness-16.exe   \
		converter-statefulness-32.exe   \
		one-beat.exe                    \
		n-beat.exe                      \
		seek_character_index.exe        \
		seek_character_index-zikzak.exe \
		Buffer_move_forward.exe         \
		Buffer_tell_and_seek.exe        \
		Buffer_move_backward.exe

DEFS = -DQUEX_OPTION_ASSERTS \
	   -DQUEX_SETTING_BUFFER_FILLER_SEEK_TEMP_BUFFER_SIZE=6 \
       -DQUEX_SETTING_BUFFER_MIN_FALLBACK_N=0 \
	   -DQUEX_OPTION_CONVERTER_ICU 

# Use 'icu-config --ldflags' in order to get the linker flags
ICU_FLAGS := $(shell icu-config --ldflags --cppflags) 

all: $(FILES)

CC = \
	g++ -I$(QUEX_PATH) $(DEFS) \
		-ggdb  \
		-Wall -Werror \
        -Werror-implicit-function-declaration 

all: $(FILES)

hwut-info:
	@echo $(FILES)

hwut-end: clean
	@echo Bye

HEADER            := \<quex\/code_base\/buffer\/converter\/icu\/Converter_ICU\.i\>
CONVERTER         := QUEX_NAME(Converter_ICU_convert)
NEW_OPERATOR      := QUEX_NAME(Converter_ICU_new)
FILLER_TYPE       := QUEX_TYPE_BUFFER_FILLER_CONVERTER_ICU
UCS_4_BYTE_BE     := "UTF32-BE"
UCS_4_BYTE_LE     := "UTF32-LE"
UCS_2_BYTE_LE     := "UTF16-LE"
UCS_UTF8          := "UTF-8"
TEST_TEMPLATE_DIR := ../../TEST-TEMPLATE/#

include $(TEST_TEMPLATE_DIR)/Makefile

%.exe: %.cpp 
	$(CC) $< -o $@ \
        -DQUEX_TYPE_CHARACTER=uint32_t \
		$(ICU_FLAGS) 

%-16.exe: %.cpp 
	$(CC) $< -o $@ \
        -DQUEX_TYPE_CHARACTER=uint16_t \
		$(ICU_FLAGS) 

%-32.exe: %.cpp 
	$(CC) $< -o $@ \
        -DQUEX_TYPE_CHARACTER=uint32_t \
		$(ICU_FLAGS) 

seek_character_index-zikzak.exe: seek_character_index-zikzak.cpp 
	$(CC) $< -o $@ \
		-DQUEX_TYPE_CHARACTER=uint16_t \
		$(ICU_FLAGS) 

clean:
	rm -f $(FILES)
	rm -f $(TEST_TEMPLATE_RESULTS)
