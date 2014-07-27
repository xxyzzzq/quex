ENGINE = \
		boeck_Lexer.c   

ifdef ASSERTS_ENABLED_F
	CCFLAG_ASSERTS=# By default asserts are enabled
else 
	CCFLAG_ASSERTS=-DQUEX_OPTION_ASSERTS_DISABLED
endif

CC := gcc -Wall -Werror -ggdb -DQUEX_OPTION_MULTI

lexer: $(ENGINE:.c=.o) lexer.o Common-token.o
	$(CC) $^ -o  $@ `icu-config --ldflags` -I$(QUEX_PATH) 
	 
%.o: %.c 
	$(CC) -c $< -ggdb -Wall -Werror -DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED -o $@ \
		-I$(QUEX_PATH)          \
		$(CCFLAG_ASSERTS) 

# -DQUEX_OPTION_ASSERTS_DISABLED
# -DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED 

COMMON_TOKEN_OPTIONS = \
	 --token-class-file Common-token.h \
     --token-policy single --suppress 5
		 # --no-message-on-extra-options \

%.E: %.c
	gcc -E $< -o  $@ -I$(QUEX_PATH) 
	
boeck_Lexer.c:  boeck.qx Common-token.c Common-token_ids
	quex -i $< -o boeck::Lexer --icu -b 4 $(COMMON_TOKEN_OPTIONS) --language C --suppress 15 --no-string-accumulator # --debug-exception

Common-token_ids \
Common-token.c: 
	quex -i token_ids.qx token_type.qx \
		 --icu -b 4                    \
		 --token-id-prefix TKN_        \
		 -o Common                     \
		 --token-class Common::Token   \
		 --token-class-only            \
	     --debug-exception \
		 --language C 

clean:
	rm -rf boeck_Lexer*
	rm -rf Common-token*
	rm -rf lexer
	rm -rf *.E
	rm -rf *.o
