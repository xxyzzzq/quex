include $(QUEX_PATH)/quex/code_base/core.mkd

TESTS = \
		simple-queue.exe \
		simple.exe

ENGINE = Simple-core-engine.cpp Simple.cpp

all: $(TESTS)

CC = g++ -ggdb -Wall \
	 -DQUEX_SETTING_TOKEN_QUEUE_SIZE=3 \
	 -DQUEX_SETTING_TOKEN_QUEUE_SAFETY_BORDER=0 \
	 -DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED \

hwut-info:
	@echo $(TESTS)

simple-queue.exe: lexer.cpp $(QUEX_CORE)
	quex -i simple.qx -o Simple --token-policy queue
	$(CC) -DTEST_simple \
		  -I$(QUEX_PATH) lexer.cpp $(ENGINE) -o $@

simple.exe:       lexer.cpp $(QUEX_CORE)
	quex -i simple.qx -o Simple --token-policy users_token
	$(CC) -DTEST_simple_queue \
		  -I$(QUEX_PATH) lexer.cpp $(ENGINE) -o $@

%.E: %.cpp
	$(CC) -E -I$(QUEX_PATH) $< -o $@

%.o: %.cpp

clean:
	rm -rf Simple*
	rm -rf $(TESTS)
	rm -rf *.o
