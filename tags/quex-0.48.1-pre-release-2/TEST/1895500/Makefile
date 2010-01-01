X = IndigoLexer

all: $(X).cpp 
	g++ -I./ -I$(QUEX_PATH) \
		$(X).cpp                      \
		lexer.cpp                     \
		-ggdb \
	   	# -D__QUEX_OPTION_DEBUG_STATE_TRANSITION_REPORTS \
		# -D__QUEX_OPTION_UNIT_TEST_INPUT_STRATEGY_ICONV 


$(X).cpp: indigo.qx
	quex -i indigo.qx -o $(X) -b 4 --iconv 


clean:
	rm -rf $(X)-*
	rm -rf $(X).cpp
	rm -rf $(X)
	rm -rf a.out
