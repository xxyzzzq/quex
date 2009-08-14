X = Simple

all: $(X).cpp 
	@echo "Compiling"
	@g++ -I./ -I$(QUEX_PATH) \
		$(X)-core-engine.cpp          \
		$(X).cpp                      \
		lexer.cpp                     \
		-ggdb \
	   	#-D__QUEX_OPTION_DEBUG_STATE_TRANSITION_REPORTS \
		# -D__QUEX_OPTION_UNIT_TEST_INPUT_STRATEGY_ICONV 


$(X).cpp: simple.qx
	@echo "Call to quex"
	@quex -i $< -o $(X) -b wchar_t --iconv --token-queue


clean:
	rm -rf $(X)-core-engine.cpp
	rm -rf $(X)-token_ids
	rm -rf $(X).cpp
	rm -rf $(X)
	rm -rf a.out
