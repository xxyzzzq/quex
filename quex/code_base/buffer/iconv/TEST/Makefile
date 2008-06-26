FILES = one-beat n-beat

all: $(FILES)

hwut-info:
	@echo $(FILES)

%: %.cpp ../fixed_size_character_stream
	g++ -I$(QUEX_PATH) \
		-ggdb \
		-D__QUEX_OPTION_UNIT_TEST_INPUT_STRATEGY_ICONV $< -o $@


clean:
	rm -f $(FILES)
