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


Simple.c: test.qx
	@echo "Call to quex"
	quex -i $< -o Simple --language C --debug-exception


clean:
	rm -rf Simple*
	rm -rf a.out
	touch test.qx
