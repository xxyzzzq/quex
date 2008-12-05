INPUT=newline-skipper-utf8 # This is overidden by a command line argument of the for INPUT=something

all: $(INPUT)

newline-skipper: 
	quex -i newline-skipper.qx -o Simple --token-prefix COL_
	g++ -I$(QUEX_PATH) -I./ Simple*.cpp lexer.cpp -ggdb -o lexer \
		-DQUEX_OPTION_LINE_NUMBER_COUNTING \
		-DQUEX_OPTION_COLUMN_NUMBER_COUNTING \
		-DQUEX_SETTING_BUFFER_SIZE=4

newline-skipper-utf8: 
	quex -i newline-skipper-utf8.qx -o Simple --token-prefix COL_ --iconv
	g++ -I$(QUEX_PATH) -I./ lexer.cpp Simple*.cpp -ggdb -o lexer \
		-DQUEX_OPTION_LINE_NUMBER_COUNTING \
		-DQUEX_OPTION_COLUMN_NUMBER_COUNTING \
		-D__QUEX_OPTION_UNIT_TEST_UTF8__ \
		-DQUEX_SETTING_BUFFER_SIZE=1000 

non-newline-skipper: 
	quex -i non-newline-skipper.qx -o Simple --token-prefix COL_
	g++ -I$(QUEX_PATH) -I./ Simple*.cpp lexer.cpp -ggdb -o lexer \
		-DQUEX_OPTION_LINE_NUMBER_COUNTING \
		-DQUEX_OPTION_COLUMN_NUMBER_COUNTING \
		-DQUEX_SETTING_BUFFER_SIZE=4

clean:
	rm -f lexer Simple*
