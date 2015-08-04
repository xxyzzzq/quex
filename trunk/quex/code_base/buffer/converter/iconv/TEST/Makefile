include $(QUEX_PATH)/quex/code_base/core.mkd

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
	   -DQUEX_OPTION_CONVERTER_ICONV 

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

HEADER            := \<quex\/code_base\/buffer\/converter\/iconv\/Converter_IConv\.i\>
CONVERTER         := QUEX_NAME(Converter_IConv_convert)
NEW_OPERATOR      := QUEX_NAME(Converter_IConv_new)
FILLER_TYPE       := QUEX_TYPE_BUFFER_FILLER_CONVERTER_ICONV
UCS_4_BYTE_BE     := "UCS-4BE"
UCS_4_BYTE_LE     := "UCS-4LE"
UCS_2_BYTE_LE     := "UCS-2LE"
UCS_UTF8          := "UTF8"
TEST_TEMPLATE_DIR := ../../TEST-TEMPLATE/#

include $(TEST_TEMPLATE_DIR)/Makefile

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
	rm -f $(TEST_TEMPLATE_RESULTS)
