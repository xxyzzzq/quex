
lexer-iconv: Simple.cpp
	@g++ -I./ -I$(QUEX_PATH) \
		Simple.cpp     \
		../lexer.cpp        \
		-ggdb               \
		-o $@               \
		-D__QUEX_OPTION_UNIT_TEST_INPUT_STRATEGY_ICONV > tmp.txt 2>&1
	@cat tmp.txt
	@rm  tmp.txt
	
lexer-icu: Simple.cpp
	@g++ -I./ -I$(QUEX_PATH) \
		Simple.cpp     \
		../lexer.cpp           \
		-ggdb               \
		-o $@               \
		-D__QUEX_OPTION_UNIT_TEST_INPUT_STRATEGY_ICU > tmp.txt 2>&1
	@cat tmp.txt
	@rm  tmp.txt

Simple.cpp: indigo.qx
	@quex -i indigo.qx -o Simple -b 4 --iconv 


clean:
	@rm -rf Simple*
	@rm -rf a.out lexer-icu lexer-iconv
