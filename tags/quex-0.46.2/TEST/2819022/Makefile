lexer: 
	quex -i error-$(CASE).qx -o Simple
	g++ -I$(QUEX_PATH) -I. \
		-DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED \
		lexer.cpp Simple.cpp Simple-core-engine.cpp \
		-Wall \
		-o lexer

Simple.E:
	g++ -c -E -I$(QUEX_PATH) -I. \
		-DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED \
		Simple.h -o $@

clean: 
	rm -f *.o
	rm -f Simple*
	rm -f lexer
