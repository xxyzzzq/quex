include $(QUEX_PATH)/quex/code_base/core.mkd

TESTS = \
		queue.exe \
		queue-real.exe \
		users_token.exe \
		users_token-real.exe \

ENGINE = TPLex.cpp

all: $(TESTS)

CCX = g++ -ggdb -Wall \
	 -DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED \
	 -DQUEX_SETTING_TOKEN_QUEUE_SIZE=5 #

CC = $(CCX) \
	 -DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED \
	 -DQUEX_SETTING_TOKEN_QUEUE_SIZE=5 \
	 -DQUEX_SETTING_TOKEN_QUEUE_SAFETY_BORDER=4 #

hwut-info:
	@echo $(TESTS)

queue.exe:            lexer.cpp $(QUEX_CORE)
	quex -i simple.qx -o TPLex --token-policy queue
	$(CC) -I$(QUEX_PATH) -D__QUEX_OPTION_TEST_PSEUDO_ANALYSIS lexer.cpp $(ENGINE) -lefence -o $@

queue-real.exe:       lexer.cpp  $(QUEX_CORE)
	quex -i real.qx -o TPLex --token-policy queue
	$(CC) -I$(QUEX_PATH) lexer.cpp $(ENGINE) -lefence -o $@

users_token.exe:      lexer.cpp  $(QUEX_CORE)
	quex -i simple.qx -o TPLex --token-policy single
	$(CC) -I$(QUEX_PATH) -D__QUEX_OPTION_TEST_PSEUDO_ANALYSIS lexer.cpp $(ENGINE) -lefence -o $@

users_token-real.exe: lexer.cpp  $(QUEX_CORE)
	quex -i real.qx -o TPLex --token-policy single
	$(CC) -I$(QUEX_PATH) lexer.cpp $(ENGINE) -lefence -o $@

## users_queue.exe:      lexer.cpp  $(QUEX_CORE)
##	quex -i simple.qx -o TPLex --token-policy users_queue
##	$(CC) -I$(QUEX_PATH) -D__QUEX_OPTION_TEST_PSEUDO_ANALYSIS lexer.cpp $(ENGINE) -lefence -o $@

## users_queue-real.exe: lexer.cpp  $(QUEX_CORE)
##	quex -i real.qx -o TPLex --token-policy users_queue
##	$(CCX) -I$(QUEX_PATH) -DQUEX_SETTING_TOKEN_QUEUE_SAFETY_BORDER=1 lexer.cpp $(ENGINE) -lefence -o $@

%.E: %.cpp
	$(CC) -E -I$(QUEX_PATH) $< -o $@

%.o: %.cpp

clean:
	rm -rf TPLex*
	rm -rf $(TESTS)
	rm -rf *.o
