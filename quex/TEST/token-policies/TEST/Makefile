TESTS = queue.exe users_token.exe users_queue.exe

hwut-info:
	@echo $(TESTS)

queue.exe: lexer.cpp LexerWith_Queue example.txt
	echo "#include \"LexerWith_Queue\""          > test_includer.h
	echo                                         >> test_includer.h
	echo "typedef quex::LexerWith_Queue  lexer;" >> test_includer.h
	$(CC) -I$(QUEX_PATH) lexer.cpp LexerWith_Queue-core-engine.cpp LexerWith_Queue.cpp

example.txt:
	# The content of the file is meaningless, but it should exist.
	touch example.txt

LexerWith_Queue:
	quex -i simple.qx -o LexerWith_Queue      --token-policy queue

LexerWith_UsersToken:
	quex -i simple.qx -o LexerWith_UsersToken --token-policy users_token

LexerWith_UsersQueue:
	quex -i simple.qx -o LexerWith_UsersQueue --token-policy users_queue

clean:
	rm -rf LexerWith_*
	rm -rf $(TESTS)
	rm -rf *.o
	rm -rf example.txt
