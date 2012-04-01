INPUT=newline-skipper-utf8 # This is overidden by a command line argument of the for INPUT=something

all: $(INPUT)

newline-skipper: 
	@quex -i token.qx newline-skipper.qx -o Simple --token-policy single
	@g++ -I$(QUEX_PATH) -I./ Simple*.cpp ../lexer-simply.cpp -ggdb -o lexer \
		-DPRINT_LINE_COLUMN \
		-DQUEX_OPTION_LINE_NUMBER_COUNTING \
		-DQUEX_OPTION_COLUMN_NUMBER_COUNTING \
		-DQUEX_SETTING_BUFFER_SIZE=4

newline-skipper-utf8: 
	@quex -i token.qx newline-skipper-utf8.qx -o Simple --iconv -b 2 --token-policy single
	@g++ -I$(QUEX_PATH) -I./ ../lexer-simply.cpp Simple*.cpp -ggdb -o lexer \
		-DPRINT_LINE_COLUMN \
		-DCONVERTER_ENCODING='"UTF-8"' \
		-DQUEX_OPTION_LINE_NUMBER_COUNTING \
		-DQUEX_OPTION_COLUMN_NUMBER_COUNTING \
		-D__QUEX_OPTION_UNIT_TEST_UTF8__ \
		-DQUEX_SETTING_BUFFER_SIZE=1000 

non-newline-skipper: 
	@quex -i token.qx non-newline-skipper.qx -o Simple --token-policy single
	@g++ -I$(QUEX_PATH) -I./ Simple*.cpp ../lexer-simply.cpp -ggdb -o lexer \
		-DPRINT_LINE_COLUMN \
		-DQUEX_OPTION_LINE_NUMBER_COUNTING \
		-DQUEX_OPTION_COLUMN_NUMBER_COUNTING \
		-DQUEX_SETTING_BUFFER_SIZE=4

clean:
	@rm -f lexer Simple*
