all:
	quex -i error.qx -o Simple --debug-exception
	g++ -I$(QUEX_PATH) -I. *.cpp ../lexer-simply.cpp -o the_test \
		-DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED

Simple.E:
	g++ -E -I$(QUEX_PATH) -I. Simple.cpp > $@ 

clean:
	rm -f Simple*
	rm -f the_test

