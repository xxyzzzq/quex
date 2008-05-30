X = IndigoLexer

all: $(X).cpp 
	g++ -I./ -I$(QUEX_PATH) \
		$(X)-core-engine.cpp          \
		$(X).cpp                      \
		lexer.cpp                     \
		-ggdb \
	   	# -D__QUEX_OPTION_DEBUG_STATE_TRANSITION_REPORTS \
		# -D__QUEX_OPTION_UNIT_TEST_INPUT_STRATEGY_ICONV 


$(X).cpp: indigo.qx
	quex -i indigo.qx -o $(X) -b 4 --iconv --token-queue


clean:
	rm -rf $(X)-core-engine.cpp
	rm -rf $(X)-token_ids
	rm -rf $(X).cpp
	rm -rf $(X)
	rm -rf a.out
