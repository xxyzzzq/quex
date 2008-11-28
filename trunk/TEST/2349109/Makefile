INPUT=newline-skipper # This is overidden by a command line argument of the for INPUT=something

all: $(INPUT)

newline-skipper: 
	quex -i newline-skipper.qx -o Simple --token-prefix COL_
	g++ -I$(QUEX_PATH) -I./ Simple*.cpp lexer.cpp -ggdb -o lexer \
		-DQUEX_OPTION_LINE_NUMBER_COUNTING \
		-DQUEX_OPTION_COLUMN_NUMBER_COUNTING \
		-DQUEX_SETTING_BUFFER_SIZE=4
non-newline-skipper: 
	quex -i non-newline-skipper.qx -o Simple --token-prefix COL_
	g++ -I$(QUEX_PATH) -I./ Simple*.cpp lexer.cpp -ggdb -o lexer \
		-DQUEX_OPTION_LINE_NUMBER_COUNTING \
		-DQUEX_OPTION_COLUMN_NUMBER_COUNTING \
		-DQUEX_SETTING_BUFFER_SIZE=4
