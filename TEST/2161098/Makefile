INPUT=funny_comments # This is overidden by a command line argument of the for INPUT=something

all: $(INPUT)

funny_comments: 
	quex -i token.qx funny_comments.qx -o Simple --token-policy single
	g++ -I$(QUEX_PATH) -I./ Simple*.cpp ../lexer-simply.cpp -ggdb -o lexer \
		-DPRINT_LINE_COLUMN \
		-DQUEX_OPTION_LINE_NUMBER_COUNTING \
		-DQUEX_OPTION_COLUMN_NUMBER_COUNTING \
		-DQUEX_SETTING_BUFFER_SIZE=11

shell_comments: 
	quex -i token.qx shell_comments.qx -o Simple --token-policy single
	g++ -I$(QUEX_PATH) -I./ Simple*.cpp ../lexer-simply.cpp -ggdb -o lexer \
		-DPRINT_LINE_COLUMN \
		-DQUEX_OPTION_LINE_NUMBER_COUNTING \
		-DQUEX_OPTION_COLUMN_NUMBER_COUNTING \
		-DQUEX_SETTING_BUFFER_SIZE=4

c_comments: 
	quex -i token.qx c_comments.qx -o Simple --token-policy single
	g++ -I$(QUEX_PATH) -I./ Simple*.cpp ../lexer-simply.cpp -ggdb -o lexer \
		-DPRINT_LINE_COLUMN \
		-DQUEX_OPTION_LINE_NUMBER_COUNTING \
		-DQUEX_OPTION_COLUMN_NUMBER_COUNTING \
		-DQUEX_SETTING_BUFFER_SIZE=4

clean:
	rm -rf lexer
	rm -rf Simple*
