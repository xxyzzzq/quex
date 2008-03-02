FILES = one-beat n-beat

all: $(FILES)

hwut-info:
	@echo $(FILES)

%: %.cpp ../input_strategy
	g++ -I$(QUEX_PATH) \
		-D__QUEX_OPTION_UNIT_TEST_INPUT_STRATEGY_ICONV $< -o $@


clean:
	rm -f $(FILES)
