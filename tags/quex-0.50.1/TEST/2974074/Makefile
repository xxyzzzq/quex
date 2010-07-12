all:
	quex -i error.qx -o Simple 
	g++ -I$(QUEX_PATH) -I. *.cpp ../lexer-simply.cpp -o the_test \
		-DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED

clean:
	rm -f Simple*
	rm -f the_test

