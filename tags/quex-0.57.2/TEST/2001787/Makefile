X = Simple

lexer-iconv: Simple.cpp
	@g++ -I./ -I$(QUEX_PATH) \
		Simple.cpp                    \
		../lexer-simply.cpp           \
		-ggdb                         \
		-o $@                         \
		-D'CONVERTER_ENCODING="UTF8"' \
		-D__QUEX_OPTION_UNIT_TEST_INPUT_STRATEGY_ICONV >& tmp.txt
	@cat tmp.txt
	@rm  tmp.txt
	

lexer-icu: Simple.cpp
	@g++ -I./ -I$(QUEX_PATH) \
		Simple.cpp                    \
		../lexer-simply.cpp           \
		-ggdb                         \
		-o $@                         \
		-D'CONVERTER_ENCODING="UTF8"' \
		-D__QUEX_OPTION_UNIT_TEST_INPUT_STRATEGY_ICU >& tmp.txt
	@cat tmp.txt
	@rm  tmp.txt


Simple.cpp: simple.qx
	@quex -i $< -o Simple --bet wchar_t --iconv --token-policy single


clean:
	@rm -rf Simple-*
	@rm -rf Simple.cpp
	@rm -rf Simple
	@rm -rf a.out lexer-iconv lexer-icu
