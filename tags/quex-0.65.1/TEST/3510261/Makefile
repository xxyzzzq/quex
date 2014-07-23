# Leave the generated code for debugging etc.
.SECONDARY: Simple.c 

test: Simple.o lexer.o
	gcc -o $@ $^ -ggdb

%.o: %.c
	gcc -c -o $@ -I$(QUEX_PATH) -I. $<                 \
		-DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED 

%.o: ../%.c
	gcc -c -o $@ -I$(QUEX_PATH) -I. $<                 \
		-DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED \
		-DPRINT_LINE_COLUMN_NUMBER                     \
		-DPRINT_TOKEN                  

Simple.c: test.qx
	quex -i $< -o $* --language C --codec utf8

clean:
	rm -f Simple*
	rm -f test
	rm -f *.o
