.PHONY: compile-error-list

CC = g++ -I$(QUEX_PATH) -I. $(CFLAGS) -ggdb \

without-include-stack:
	quex -i simple.qx -o Simple 
	$(CC) -DQUEX_OPTION_INCLUDE_STACK_DISABLED \
		  lexer.cpp Simple*.cpp -o lexer

with-include-stack:
	quex -i simple.qx -o Simple 
	$(CC) lexer.cpp Simple*.cpp -o lexer

clean:
	rm -f Simple*
	rm -f *.o
	rm -f lexer error-lexer
