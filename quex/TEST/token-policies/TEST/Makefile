include $(QUEX_PATH)/quex/code_base/core.mkd

TESTS = \
		queue.exe \
		users_token.exe \
		users_queue.exe \
		queue-real.exe \
		users_token-real.exe \
		users_queue-real.exe

ENGINE = TPLex-core-engine.cpp TPLex.cpp

all: $(TESTS)

CC = g++ -ggdb -Wall \
	 -DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED \
	 -DQUEX_SETTING_TOKEN_QUEUE_SIZE=5 \
	 -DQUEX_SETTING_TOKEN_QUEUE_SAFETY_BORDER=4 

hwut-info:
	@echo $(TESTS)

queue.exe: lexer.cpp 
	quex -i simple.qx -o TPLex --token-policy queue
	$(CC) -I$(QUEX_PATH) -D__QUEX_OPTION_TEST_PSEUDO_ANALYSIS lexer.cpp $(ENGINE) -o $@

users_token.exe: lexer.cpp 
	quex -i simple.qx -o TPLex --token-policy users_token
	$(CC) -I$(QUEX_PATH) -D__QUEX_OPTION_TEST_PSEUDO_ANALYSIS lexer.cpp $(ENGINE) -o $@

users_queue.exe: lexer.cpp 
	quex -i simple.qx -o TPLex --token-policy users_queue
	$(CC) -I$(QUEX_PATH) -D__QUEX_OPTION_TEST_PSEUDO_ANALYSIS lexer.cpp $(ENGINE) -o $@

queue-real.exe: lexer.cpp 
	$(CC) -I$(QUEX_PATH) lexer.cpp $(ENGINE) -o $@

users_token-real.exe: lexer.cpp 
	quex -i real.qx -o TPLex --token-policy users_token
	$(CC) -I$(QUEX_PATH) lexer.cpp $(ENGINE) -o $@

users_queue-real.exe: lexer.cpp 
	quex -i real.qx -o TPLex --token-policy users_queue
	$(CC) -I$(QUEX_PATH) lexer.cpp $(ENGINE) -o $@

%.E: %.cpp
	$(CC) -E -I$(QUEX_PATH) $< -o $@

%.o: %.cpp

clean:
	rm -rf TPLex*
	rm -rf $(TESTS)
	rm -rf *.o
