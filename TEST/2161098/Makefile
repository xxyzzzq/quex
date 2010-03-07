INPUT=funny_comments # This is overidden by a command line argument of the for INPUT=something

all: $(INPUT)

funny_comments: 
	quex -i funny_comments.qx -o Simple --token-prefix COL_ --token-policy single
	g++ -I$(QUEX_PATH) -I./ Simple*.cpp lexer.cpp -ggdb -o lexer \
		-DQUEX_OPTION_LINE_NUMBER_COUNTING \
		-DQUEX_OPTION_COLUMN_NUMBER_COUNTING \
		-DQUEX_SETTING_BUFFER_SIZE=11
shell_comments: 
	quex -i shell_comments.qx -o Simple --token-prefix COL_ --token-policy single
	g++ -I$(QUEX_PATH) -I./ Simple*.cpp lexer.cpp -ggdb -o lexer \
		-DQUEX_OPTION_LINE_NUMBER_COUNTING \
		-DQUEX_OPTION_COLUMN_NUMBER_COUNTING \
		-DQUEX_SETTING_BUFFER_SIZE=4
c_comments: 
	quex -i c_comments.qx -o Simple --token-prefix COL_ --token-policy single
	g++ -I$(QUEX_PATH) -I./ Simple*.cpp lexer.cpp -ggdb -o lexer \
		-DQUEX_OPTION_LINE_NUMBER_COUNTING \
		-DQUEX_OPTION_COLUMN_NUMBER_COUNTING \
		-DQUEX_SETTING_BUFFER_SIZE=4

clean:
	rm -rf lexer
	rm -rf Simple*
