FILES = one-beat.exe n-beat.exe

DEFS = -DQUEX_OPTION_ASSERTS \
       -DQUEX_CHARACTER_TYPE=uint32_t \
       -DQUEX_SETTING_BUFFER_MIN_FALLBACK_N=0 

HEADERS = #

all: $(FILES)

hwut-info:
	@echo $(FILES)

%.exe: %.cpp $(HEADERS)
	g++ -I$(QUEX_PATH) $(DEFS) \
		-ggdb  \
		-D__QUEX_OPTION_UNIT_TEST_INPUT_STRATEGY_ICONV $< -o $@


clean:
	rm -f $(FILES)
