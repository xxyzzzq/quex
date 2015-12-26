# PURPOSE: Building applications for massive seek&tell tests on the Buffer-seek.
#          
# Buffer seeking sets the 'read_p' to a specific character index. It includes
# loading the required content into the buffer's engine. The test depends on
# the size of a character and the fallback number (number of characters left
# in front, to prevent permanent backward loading).
#
# The files in this directory check on different filler types. They do not
# check on different byte-loader types. Byte-loading is extensively tested
# elsewhere.
# 
# QUEX_TYPE_CHARACTER and QUEX_SETTING_BUFFER_MIN_FALLBACK_N are controlled
# at compile time. Thus, to variate those two, different test object files 
# must be build from ONE source file. Therefore, for each combination a rule
# exists that produces the object file. Rules follow the scheme:
#
#              %-SIZE-FALLBACK_.exe: %.cpp
#
# with SIZE as sizeof(QUEX_TYPE_CHARACTER) and FALLBACK_ as the value of 
# QUEX_SETTING_BUFFER_MIN_FALLBACK_N.
#
# (C) Frank-Rene Schaefer
#______________________________________________________________________________

TESTS := \
	     $(foreach S, 1 2 4, $(foreach FB, 0 1 2, test-Plain-$(S)-$(FB).exe)) \
	     $(foreach S, 1 2 4, $(foreach FB, 0 1 2, test-Converter-$(S)-$(FB).exe)) \
	     $(foreach FB, 0 1 2, test-Plain-wiostream-2-$(FB).exe)

DEFS       := -DQUEX_OPTION_ASSERTS \
              -DQUEX_SETTING_BUFFER_FILLER_SEEK_TEMP_BUFFER_SIZE=5 \
			  -DQUEX_OPTION_CONVERTER_ICONV \
			  -DQUEX_OPTION_CONVERTER_ICU 
INCLUDES   := -I. -I$(HWUT_PATH)/support/C -I$(QUEX_PATH)

SIZE_1     := -DQUEX_TYPE_CHARACTER=uint8_t
SIZE_2     := -DQUEX_TYPE_CHARACTER=uint16_t
SIZE_4     := -DQUEX_TYPE_CHARACTER=uint32_t
SIZE_WC    := -DQUEX_TYPE_CHARACTER=wchar_t
FALLBACK_0 := -DQUEX_SETTING_BUFFER_MIN_FALLBACK_N=0 
FALLBACK_1 := -DQUEX_SETTING_BUFFER_MIN_FALLBACK_N=1 
FALLBACK_2 := -DQUEX_SETTING_BUFFER_MIN_FALLBACK_N=2

CFLAGS := -ggdb -Wall -Werror $(INCLUDES) $(DEFS) \
	      -fsanitize=address basic_functionality.c
CC     := gcc $(CFLAGS) -D__QUEX_OPTION_PLAIN_C -Wall -Werror
CCP    := g++ $(CFLAGS) -Wall -Werror

XLIBS := $(shell icu-config --ldflags) 

all: $(TESTS)

hwut-info:
	@echo $(TESTS)

hwut-end: clean

# RULES _______________________________________________________________________
#
%-4-0.exe: %.c basic_functionality.c
	$(CC) $(SIZE_4) $(FALLBACK_0) $< $(XLIBS) -o $@ 
%-4-1.exe: %.c basic_functionality.c
	$(CC) $(SIZE_4) $(FALLBACK_1) $< $(XLIBS) -o $@
%-4-2.exe: %.c basic_functionality.c
	$(CC) $(SIZE_4) $(FALLBACK_2) $< $(XLIBS) -o $@

%-2-0.exe: %.c basic_functionality.c
	$(CC) $(SIZE_2) $(FALLBACK_0) $< $(XLIBS) -o $@
%-2-1.exe: %.c basic_functionality.c
	$(CC) $(SIZE_2) $(FALLBACK_1) $< $(XLIBS) -o $@
%-2-2.exe: %.c basic_functionality.c
	$(CC) $(SIZE_2) $(FALLBACK_2) $< $(XLIBS) -o $@

%-2-0.exe: %.cpp basic_functionality.c
	$(CCP) $(SIZE_WC) $(FALLBACK_0) $< $(XLIBS) -o $@
%-2-1.exe: %.cpp basic_functionality.c
	$(CCP) $(SIZE_WC) $(FALLBACK_1) $< $(XLIBS) -o $@
%-2-2.exe: %.cpp basic_functionality.c
	$(CCP) $(SIZE_WC) $(FALLBACK_2) $< $(XLIBS) -o $@

%-1-0.exe: %.c basic_functionality.c
	$(CC) $(SIZE_1) $(FALLBACK_0) $< $(XLIBS) -o $@
%-1-1.exe: %.c basic_functionality.c
	$(CC) $(SIZE_1) $(FALLBACK_1) $< $(XLIBS) -o $@
%-1-2.exe: %.c basic_functionality.c
	$(CC) $(SIZE_1) $(FALLBACK_2) $< $(XLIBS) -o $@


%.E: %.c
	$(CC) $(DEFS) $(INCLUDES) -E $< -o $@

%.E: %.cpp
	g++ $(DEFS) $(INCLUDES) -E $< -o $@

clean: 
	rm -rf $(TESTS) *.o *.E
