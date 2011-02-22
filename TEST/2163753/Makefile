X = Simple

all: $(X).cpp 
	@echo "Compiling"
	@g++ -I./ -I$(QUEX_PATH) \
		$(X).cpp             \
		../lexer-simply.cpp  \
		-ggdb \
		-DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED
	   	#-DQUEX_OPTION_DEBUG_SHOW \
		# -D__QUEX_OPTION_UNIT_TEST_INPUT_STRATEGY_ICONV 


$(X).cpp: simple.qx
	@echo "Call to quex"
	@quex -i $< -o $(X) 


clean:
	rm -rf $(X)-*
	rm -rf $(X).cpp
	rm -rf $(X)
	rm -rf a.out
	touch simple.qx
