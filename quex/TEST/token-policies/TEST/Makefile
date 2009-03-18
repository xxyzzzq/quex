TESTS = queue.exe users_token.exe users_queue.exe

all: $(TESTS)

CC = g++ -ggdb -Wall \
	 -DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED \
	 -DQUEX_SETTING_TOKEN_QUEUE_SIZE=5 \
	 -DQUEX_SETTING_TOKEN_QUEUE_SAFETY_BORDER=2 

QUEUE_ENGINE  = LexerWith_Queue.o      LexerWith_Queue-core-engine.o
UTOKEN_ENGINE = LexerWith_UsersToken.o LexerWith_UsersToken-core-engine.o
UQUEUE_ENGINE = LexerWith_UsersQueue.o LexerWith_UsersQueue-core-engine.o

hwut-info:
	@echo $(TESTS)

queue.exe: lexer.cpp $(QUEUE_ENGINE) example.txt
	echo "#include \"LexerWith_Queue\""          > test_includer.h
	echo                                         >> test_includer.h
	echo "typedef quex::LexerWith_Queue  lexer;" >> test_includer.h
	$(CC) -I$(QUEX_PATH) lexer.cpp $(QUEUE_ENGINE) -o $@

LexerWith_Queue.cpp \
LexerWith_Queue-core-engine.cpp:
	quex -i simple.qx -o LexerWith_Queue      --token-policy queue

users_token.exe: lexer.cpp $(UTOKEN_ENGINE) example.txt
	echo "#include \"LexerWith_UsersToken\""          > test_includer.h
	echo                                              >> test_includer.h
	echo "typedef quex::LexerWith_UsersToken  lexer;" >> test_includer.h
	$(CC) -I$(QUEX_PATH) lexer.cpp $(UTOKEN_ENGINE) -o $@

LexerWith_UsersToken.cpp \
LexerWith_UsersToken-core-engine.cpp:
	quex -i simple.qx -o LexerWith_UsersToken --token-policy users_token

users_queue.exe: lexer.cpp  $(UQUEUE_ENGINE) example.txt
	echo "#include \"LexerWith_UsersQueue\""          > test_includer.h
	echo                                              >> test_includer.h
	echo "typedef quex::LexerWith_UsersQueue  lexer;" >> test_includer.h
	$(CC) -I$(QUEX_PATH) lexer.cpp $(UQUEUE_ENGINE) -o $@

LexerWith_UsersQueue.cpp \
LexerWith_UsersQueue-core-engine.cpp:
	quex -i simple.qx -o LexerWith_UsersQueue --token-policy users_queue

%.E: %.cpp
	$(CC) -E -I$(QUEX_PATH) $< -o $@

%.o: %.cpp
	$(CC) -c -I$(QUEX_PATH) $< -o $@

example.txt:
	# The content of the file is meaningless, but it should exist.
	touch example.txt

clean:
	rm -rf LexerWith_*
	rm -rf $(TESTS)
	rm -rf *.o
	rm -rf example.txt
	rm -rf test_includer.h
