CFLAGS:=-Wimplicit
QUEX_PARAMS:=-DQUEX_OPTION_ASSERTS_DISABLED -DQUEX_SETTING_BUFFER_MIN_FALLBACK_N=0 #-DQUEX_OPTION_DEBUG_SHOW

%.E: %.c
	gcc -E -I$(QUEX_PATH) $(QUEX_PARAMS) -I. $(CFLAGS) $< -o $@

%.c: %.qx Makefile
	quex -i $< \
		 --token-policy single \
		 --language C \
		 --token-memory-management-by-user \
		-o $(basename $@)

%.o: %.c Makefile
	gcc -ggdb -I$(QUEX_PATH) $(QUEX_PARAMS) -I. $(CFLAGS) -c $< -o $@

.PHONY: clean all
all: simple.o main.o
	gcc -o lexer simple.o main.o

clean:
	touch simple.qx
	rm -f simple.h simple.c simple-configuration.h simple-token.h simple-token_ids.h
	rm -f *.o
	rm -f lexer

main.o: simple.c
