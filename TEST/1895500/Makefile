X = IndigoLexer

lexer-iconv: IndigoLexer.cpp
	@g++ -I./ -I$(QUEX_PATH) \
		IndigoLexer.cpp     \
		../lexer.cpp        \
		-ggdb               \
		-o $@               \
		-D__QUEX_OPTION_UNIT_TEST_INPUT_STRATEGY_ICONV >& tmp.txt
	@cat tmp.txt
	@rm  tmp.txt
	
lexer-icu: IndigoLexer.cpp
	@g++ -I./ -I$(QUEX_PATH) \
		IndigoLexer.cpp     \
		../lexer.cpp           \
		-ggdb               \
		-o $@               \
		-D__QUEX_OPTION_UNIT_TEST_INPUT_STRATEGY_ICU >& tmp.txt
	@cat tmp.txt
	@rm  tmp.txt

IndigoLexer.cpp: indigo.qx
	@quex -i indigo.qx -o IndigoLexer -b 4 --iconv 


clean:
	@rm -rf IndigoLexer-*
	@rm -rf IndigoLexer.cpp
	@rm -rf IndigoLexer
	@rm -rf a.out
