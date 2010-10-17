INPUT=funny_comments # This is overidden by a command line argument of the for INPUT=something

DEFINES = \
		-DPRINT_LINE_COLUMN \
		-DQUEX_OPTION_LINE_NUMBER_COUNTING \
		-DQUEX_OPTION_COLUMN_NUMBER_COUNTING \

CC = g++ -I$(QUEX_PATH) -I./ -ggdb -o lexer

all: $(INPUT)

funny_comments: 
	quex -i token.qx $(PREFIX)funny_comments.qx -o Simple --token-policy single
	$(CC) Simple*.cpp ../lexer-simply.cpp \
		$(DEFINES) -DQUEX_SETTING_BUFFER_SIZE=11

shell_comments: 
	quex -i token.qx $(PREFIX)shell_comments.qx -o Simple --token-policy single
	$(CC) Simple*.cpp ../lexer-simply.cpp \
		$(DEFINES) -DQUEX_SETTING_BUFFER_SIZE=4

c_comments: 
	quex -i token.qx $(PREFIX)c_comments.qx     -o Simple --token-policy single
	$(CC) Simple*.cpp ../lexer-simply.cpp \
		$(DEFINES) -DQUEX_SETTING_BUFFER_SIZE=4

## $(DEFINES) -DQUEX_SETTING_BUFFER_SIZE=1024

clean:
	rm -rf lexer
	rm -rf Simple*
