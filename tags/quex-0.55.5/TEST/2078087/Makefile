.PHONY: lexer

CFLAGS = \
	 -DQUEX_OPTION_DEBUG_MODE_TRANSITIONS \
     -DQUEX_OPTION_LINE_NUMBER_COUNTING_DISABLED \
     -DQUEX_OPTION_COLUMN_NUMBER_COUNTING_DISABLED \
	 #-D__QUEX_OPTION_DEBUG_STATE_TRANSITION_REPORTS

lexer:
	quex -i $(INPUT) -o Simple --token-policy single
	g++ -I$(QUEX_PATH) -I. \
		$(CFLAGS) \
		../lexer-simply.cpp Simple*.cpp \
		-ggdb -o lexer

lexer.E:
	quex -i $(INPUT) -o Simple --token-policy single
	g++ -I$(QUEX_PATH) -I. \
		-E $(CFLAGS) \
		../lexer-simply.cpp \
		-ggdb -o lexer.E
