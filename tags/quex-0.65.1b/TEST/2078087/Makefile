.PHONY: lexer

CFLAGS = \
	 -DQUEX_OPTION_DEBUG_SHOW_MODES \
     -DQUEX_OPTION_LINE_NUMBER_COUNTING_DISABLED \
     -DQUEX_OPTION_COLUMN_NUMBER_COUNTING_DISABLED \
	 #-DQUEX_OPTION_DEBUG_SHOW

lexer:
	quex -i $(INPUT) -o Simple --token-policy single --language C --debug-exception
	g++ -I$(QUEX_PATH) -I. \
		-DPRINT_TOKEN \
		$(CFLAGS) \
		../lexer.c Simple*.c \
		-ggdb -o lexer

lexer.E:
	quex -i $(INPUT) -o Simple --token-policy single --language C --debug-exception
	g++ -I$(QUEX_PATH) -I. \
		-E $(CFLAGS) \
		../lexer.c \
		-ggdb -o lexer.E
