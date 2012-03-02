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
	$(QUEX_PATH)/quex-exe.py --token-policy single \
		                     --codec utf8          \
							 -b 1                  \
							 -i $<                 \
							 -o $*                 \
							 --language C

clean:
	rm -f Simple*
	rm -f test
	rm -f *.o
