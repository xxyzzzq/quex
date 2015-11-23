ENGINE = \
		boeck_Lexer.c   \
		max_Lexer.c     \
		moritz_Lexer.c  

ifdef ASSERTS_ENABLED_F
	CCFLAG_ASSERTS=# By default asserts are enabled
else 
	CCFLAG_ASSERTS=-DQUEX_OPTION_ASSERTS_DISABLED
endif

CC := gcc -ggdb -Wall -Werror -DQUEX_OPTION_MULTI 

lexer: $(ENGINE:.c=.o) lexer.o A_B_C-token.o
	$(CC) $^ -o  $@ -I$(QUEX_PATH) `icu-config --ldflags` 
	 
%.o: %.c $(ENGINE)
	$(CC) -c $< -o $@ -I$(QUEX_PATH) $(CCFLAG_ASSERTS) 

# -DQUEX_OPTION_ASSERTS_DISABLED
# -DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED 

COMMON_TOKEN_OPTIONS = \
	 --token-class-file A_B_C-token.h \
     --token-policy     single \
	 --suppress         0 1 6
		 # --no-message-on-extra-options \

%.E: %.c
	gcc -E $< -o  $@ -I$(QUEX_PATH)
	
boeck_Lexer.c:  boeck.qx A_B_C-token.c A_B_C-token_ids.h
	quex -i $< -o boeck::Lexer --icu -b 4 $(COMMON_TOKEN_OPTIONS) --language C

max_Lexer.c:    max.qx A_B_C-token.c A_B_C-token_ids.h
	quex -i $< -o max::Lexer --icu -b 4 $(COMMON_TOKEN_OPTIONS) --language C 

moritz_Lexer.c: moritz.qx A_B_C-token.c A_B_C-token_ids.h
	quex -i $< -o moritz::Lexer --icu -b 4 $(COMMON_TOKEN_OPTIONS) --language C 

A_B_C-token_ids.h \
A_B_C-token.c: 
	quex -i token_ids.qx               \
		 --language C                  \
		 --icu -b 4                    \
		 --token-id-prefix TKN_        \
		 -o A::B::C                    \
		 --token-class A::B::C::Token  \
		 --token-class-only            

clean:
	rm -rf $(ENGINE)
	rm -rf $(ENGINE:.c=.o)
	rm -rf $(ENGINE:.c=.h)
	rm -rf $(ENGINE:.c=-token_ids.h)
	rm -rf $(ENGINE:.c=-token.h)
	rm -rf $(ENGINE:.c=-configuration.h)
	rm -rf A_B_C-token*
	rm -rf lexer
	rm -rf *.E
	rm -rf lexer.o
