TESTS = queue.exe users_token.exe users_queue.exe

all: $(TESTS)

CC = g++ -ggdb

hwut-info:
	@echo $(TESTS)

queue.exe: lexer.cpp LexerWith_Queue.o LexerWith_Queue-core-engine.o example.txt
	echo "#include \"LexerWith_Queue\""          > test_includer.h
	echo                                         >> test_includer.h
	echo "typedef quex::LexerWith_Queue  lexer;" >> test_includer.h
	$(CC) -I$(QUEX_PATH) lexer.cpp LexerWith_Queue-core-engine.o LexerWith_Queue.o -o $@

%.o: %.cpp
	$(CC) -c -I$(QUEX_PATH) $< -o $@

example.txt:
	# The content of the file is meaningless, but it should exist.
	touch example.txt

LexerWith_Queue.cpp \
LexerWith_Queue-core-engine.cpp:
	quex -i simple.qx -o LexerWith_Queue #     --token-policy queue

LexerWith_UsersToken.cpp:
	quex -i simple.qx -o LexerWith_UsersToken --token-policy users_token

LexerWith_UsersQueue.cpp:
	quex -i simple.qx -o LexerWith_UsersQueue --token-policy users_queue

clean:
	rm -rf LexerWith_*
	rm -rf $(TESTS)
	rm -rf *.o
	rm -rf example.txt
	rm -rf test_includer.h
