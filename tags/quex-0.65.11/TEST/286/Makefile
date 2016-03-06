lexer: lexer.cpp tokenizer_it.cpp
	g++ -I$(QUEX_PATH) -I. $^ -o $@ -ggdb

tokenizer_it.cpp: simple.qx
	quex -i simple.qx -o tokenizer_it --iconv \
         --bet wchar_t \
         --token-policy single \
         --token-memory-management-by-user 

clean:
	rm -f lexer
	rm -f tokenizer_it tokenizer_it*
	rm -f *.o
