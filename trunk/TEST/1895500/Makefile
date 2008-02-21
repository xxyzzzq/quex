X = IndigoLexer

all: $(X).cpp 
	g++ -I./ -I$(QUEX_PATH) \
		-D__QUEX_OPTION_UNIT_TEST_INPUT_STRATEGY_ICONV \
		-DQUEX_SETTING_BUFFER_SIZE=32 \
		$(X)-core-engine.cpp          \
		$(X).cpp                      \
		lexer.cpp                     \
		-ggdb


$(X).cpp: indigo.quex
	quex -i indigo.quex -o $(X) -b 4 --iconv


clean:
	rm -rf $(X)-core-engine.cpp
	rm -rf $(X)-token_ids
	rm -rf $(X).cpp
	rm -rf $(X)
