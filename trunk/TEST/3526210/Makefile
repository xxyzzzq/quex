all: string.qx main.c
	quex -i string.qx --language C -o ::Lexer --debug-exception
	gcc *.c -o string -I$(QUEX_PATH) -DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED -ggdb

clean:
	rm Lexer* -f
