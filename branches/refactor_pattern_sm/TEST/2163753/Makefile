X = Simple

all: $(X).c 
	@echo "Compiling"
	@gcc -I./ -I$(QUEX_PATH) \
		$(X).c             \
		../lexer.c  \
		-ggdb \
		-DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED \
		-DPRINT_TOKEN
	   	# -DQUEX_OPTION_DEBUG_SHOW 
		# -D__QUEX_OPTION_UNIT_TEST_INPUT_STRATEGY_ICONV 


$(X).c: simple.qx
	@echo "Call to quex"
	quex -i $< -o $(X) --language C


clean:
	rm -rf $(X)-*
	rm -rf $(X).[ch]
	rm -rf $(X)
	rm -rf a.out
	touch simple.qx
