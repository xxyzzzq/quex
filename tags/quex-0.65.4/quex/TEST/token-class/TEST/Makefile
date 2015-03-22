include $(QUEX_PATH)/quex/code_base/core.mkd

TESTS = \
		simple-queue.exe \
		simple.exe

ENGINE = Simple.cpp

all: $(TESTS)

CC = g++ -ggdb -Wall -Werror \
	 -DQUEX_SETTING_TOKEN_QUEUE_SIZE=3 \
	 -DQUEX_SETTING_TOKEN_QUEUE_SAFETY_BORDER=0 \
	 -DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED \

hwut-info:
	@echo $(TESTS) 

simple-queue.exe: lexer.cpp $(QUEX_CORE) token.qx send-via-name.qx
	quex -i token.qx send-via-name.qx -o Simple --token-policy queue \
		 --suppress 15
	$(CC) -I$(QUEX_PATH) lexer.cpp $(ENGINE) -o $@

simple.exe:       lexer.cpp $(QUEX_CORE) token.qx send-via-overload.qx
	quex -i token.qx send-via-overload.qx -o Simple --token-policy single \
		 --suppress 15
	$(CC) -I$(QUEX_PATH) lexer.cpp $(ENGINE) -o $@

%.E: %.cpp
	$(CC) -E -I$(QUEX_PATH) $< -o $@

%.o: %.cpp

clean:
	rm -rf Simple*
	rm -rf $(TESTS)
	rm -rf *.o
