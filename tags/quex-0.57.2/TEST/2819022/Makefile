lexer: 
	quex -i error-$(CASE).qx -o Simple
	g++ -I$(QUEX_PATH) -I. \
		-DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED \
		../lexer.cpp Simple.cpp  \
		-Wall \
		-o lexer
        # -D__QUEX_OPTION_DEBUG_STATE_TRANSITION_REPORTS \

Simple.E:
	g++ -c -E -I$(QUEX_PATH) -I. \
		-DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED \
		Simple.h -o $@

clean: 
	rm -f *.o
	rm -f Simple*
	rm -f lexer
