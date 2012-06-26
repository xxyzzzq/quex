.PHONY: SOURCES

ICU_LFLAGS=$(shell icu-config --ldflags)

test: lexer.o Simple.o
	gcc -o $@ $^ $(ICU_LFLAGS)

lexer.o: ../lexer.c SOURCES
	gcc -c -o $@ -I$$QUEX_PATH -I. -DCHARACTER_ENCODING_NAME=\"utf8\" -DPRINT_TOKEN $< -Wall

Simple.o: Simple.c SOURCES
	gcc -c -o $@ -I$$QUEX_PATH -I. $< -Wall

Simple \
Simple.cpp: SOURCES

SOURCES: 
	quex --icu -b 2 -i test.qx -o Simple --language C $(ADD_OPTION) --debug-exception

clean:
	rm -f Simple*
	rm -f *.o
	rm -f test
