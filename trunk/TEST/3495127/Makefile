all: Simple.c 
	@echo "Compiling"
	@gcc -I./ -I$(QUEX_PATH) \
		Simple.c          \
		lexer.c  \
		-ggdb \
		-DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED \
		-DPRINT_TOKEN                                  \
	    -DQUEX_OPTION_SEND_AFTER_TERMINATION_ADMISSIBLE 
		
# -DQUEX_OPTION_DEBUG_SHOW  
# -D__QUEX_OPTION_UNIT_TEST_INPUT_STRATEGY_ICONV 

Simple.E: Simple.c
	gcc -E -I./ -I$(QUEX_PATH) Simple.c -o Simple.E

Simple.c: $(TOKEN_POLICY).qx
	@echo "Call to quex"
	quex -i $(TOKEN_POLICY).qx -o Simple --language C --debug-exception --token-policy $(TOKEN_POLICY) ##

clean:
	rm -rf Simple*
	rm -rf a.out
	touch test.qx
