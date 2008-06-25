X = Simple

all: $(X).cpp text.345
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

text.345: 
	@echo "Unpacking text.345"
	@bzip2 -d text.345.bz2

clean:
	rm -rf $(X)-core-engine.cpp
	rm -rf $(X)-token_ids
	rm -rf $(X).cpp
	rm -rf $(X)
	rm -rf a.out
	bzip2 text.345
