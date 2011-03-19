lexer: simple.qx main.c
	quex -i  simple.qx -o Simple --post-categorizer --language C
	gcc -I$(QUEX_PATH) main.c Simple.c -o lexer -ggdb

clean: 
	rm -f Simple*
	rm -f lexer
