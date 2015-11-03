# Testing the implementation of the 'Converter' interface for the IConv
# library.
#
# There are three tests: 
#
#     'one-beat': The complete source is converted completely into
#                 the drain (source and drain a fully available).
#
#     'stepwise-source': The source is fed into the converter byte-
#                        by byte. So the converter must eventually
#                        wait until a character representation is
#                        complete.
#
#     'stepwise-drain': It is left only place for one character to
#                       be converted, so the converter must stop
#                       at the right source positions.
#
# (C) Frank-Rene Schaefer
#______________________________________________________________________________

FILES := $(foreach S, 1 2 4 WC, one-beat-$(S).exe)       \
	     $(foreach S, 1 2 4 WC, stepwise-drain-$(S).exe) \
	     $(foreach S, 1 2 4 WC, stepwise-source-$(S).exe) 

BASIC_SOURCES := basic_functionality.c \
	             basic_functionality-iconv.c

DEFS := -DQUEX_OPTION_ASSERTS \
	    -DQUEX_SETTING_BUFFER_FILLER_SEEK_TEMP_BUFFER_SIZE=6 \
        -DQUEX_SETTING_BUFFER_MIN_FALLBACK_N=0 \
	    -DQUEX_OPTION_CONVERTER_ICONV 

INCLUDES := -I. -I$(HWUT_PATH)/support/C -I$(QUEX_PATH)

CC = \
	g++ $(INCLUDES) $(DEFS) \
		-ggdb  \
		-Wall -Werror \
        -Werror-implicit-function-declaration 

all: $(FILES)

hwut-info:
	@echo $(FILES)

hwut-end: clean
	@echo Bye

%-1.exe: %.cpp $(BASIC_SOURCES)
	$(CC) $^ -o $@ -DQUEX_TYPE_CHARACTER=uint8_t 

%-2.exe: %.cpp $(BASIC_SOURCES)
	$(CC) $^ -o $@ -DQUEX_TYPE_CHARACTER=uint16_t 

%-4.exe: %.cpp $(BASIC_SOURCES)
	$(CC) $^ -o $@ -DQUEX_TYPE_CHARACTER=uint32_t 

%-WC.exe: %.cpp $(BASIC_SOURCES)
	$(CC) $^ -o $@ -DQUEX_TYPE_CHARACTER=wchar_t 

%.E: %.cpp
	g++ $(DEFS) $(INCLUDES) -E $< -o $@

%.E: %.c
	g++ $(DEFS) $(INCLUDES) -E $< -o $@


clean:
	rm -f $(FILES)
	rm -f *.o
	rm -f *.E
	rm -f *~
