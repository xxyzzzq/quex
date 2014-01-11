.PHONY: lexer error-lexer

CFLAGS = \
	 -DQUEX_OPTION_DEBUG_SHOW_MODES          \
     -DQUEX_OPTION_LINE_NUMBER_COUNTING_DISABLED   \
     -DQUEX_OPTION_COLUMN_NUMBER_COUNTING_DISABLED \
	 -DQUEX_SETTING_BUFFER_SIZE=128                \
     -D__QUEX_OPTION_UNIT_TEST
	 #-DQUEX_OPTION_DEBUG_SHOW

CC = g++ -I$(QUEX_PATH) -I. $(CFLAGS) -ggdb \

error-lexer:
	quex -i simple.qx -o Simple --token-policy single # --debug-exception
	$(CC) -DSTRANGE_STREAM \
	      ../lexer-simply.cpp Simple.cpp -o error-lexer

lexer:
	quex -i simple.qx -o Simple --token-policy single # --debug-exception
	$(CC) -DQUEX_OPTION_STRANGE_ISTREAM_IMPLEMENTATION \
		  -DSTRANGE_STREAM \
		  ../lexer-simply.cpp Simple.cpp -o lexer

clean:
	rm -f Simple*
	rm -f *.o
	rm -f lexer error-lexer
