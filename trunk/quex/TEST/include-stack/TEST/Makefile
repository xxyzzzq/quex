
TESTS = \
		queue.exe \
		users_token.exe \

ENGINE = ISLexer.cpp

all: $(TESTS)

CC =  \
     g++ -ggdb -Wall -Werror -fsanitize=address     \
	 -DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED \
	 -DQUEX_SETTING_TOKEN_QUEUE_SIZE=5              \
	 -DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED \
	 -DQUEX_SETTING_TOKEN_QUEUE_SIZE=5              \
	 -DQUEX_SETTING_TOKEN_QUEUE_SAFETY_BORDER=1 #
	 #-DQUEX_OPTION_DEBUG_SHOW

hwut-info:
	@echo $(TESTS)

queue.exe:       lexer.cpp simple.qx 
	quex -i simple.qx -o ISLexer --token-policy queue
	$(CC) -I$(QUEX_PATH) lexer.cpp $(ENGINE) -lefence -o $@

users_token.exe: lexer.cpp simple.qx 
	quex -i simple.qx -o ISLexer --token-policy single
	$(CC) -I$(QUEX_PATH) lexer.cpp $(ENGINE) -o $@

## User's queue has been deprecated
##
## users_queue.exe: lexer.cpp simple.qx 
##	quex -i simple.qx -o ISLexer --token-policy users_queue
##	$(CC) -I$(QUEX_PATH) lexer.cpp $(ENGINE) -o $@

%.E: %.cpp
	$(CC) -E -I$(QUEX_PATH) $< -o $@

%.o: %.cpp

clean:
	rm -rf ISLexer*
	rm -rf $(TESTS)
	rm -rf *.o
