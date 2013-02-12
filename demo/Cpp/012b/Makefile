ENGINE = \
		boeck_Lexer.cpp   \
		max_Lexer.cpp     \
		moritz_Lexer.cpp             

ifdef ASSERTS_ENABLED_F
	CCFLAG_ASSERTS=# By default asserts are enabled
else 
	CCFLAG_ASSERTS=-DQUEX_OPTION_ASSERTS_DISABLED
endif

lexer: $(ENGINE:.cpp=.o) lexer.o A_B_C-token.o
	g++ $^ -ggdb -o  $@ -I$(QUEX_PATH) `icu-config --ldflags`
	 
%.o: %.cpp $(ENGINE_SOURCES)
	g++ -c $< -ggdb -Wall -o $@ \
		-I$(QUEX_PATH) \
		$(CCFLAG_ASSERTS) 

# -DQUEX_OPTION_ASSERTS_DISABLED
# -DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED 

COMMON_TOKEN_OPTIONS = \
	 --token-class-file A_B_C-token \
     --token-policy single --suppress 0 1 6
		 # --no-message-on-extra-options \

%.E: %.cpp
	g++ -E $< -o  $@ -I$(QUEX_PATH) 
	
boeck_Lexer.cpp:  boeck.qx A_B_C-token.cpp A_B_C-token_ids
	quex -i $< -o boeck::Lexer --icu -b 4 $(COMMON_TOKEN_OPTIONS) 

max_Lexer.cpp:    max.qx A_B_C-token.cpp A_B_C-token_ids
	quex -i $< -o max::Lexer --icu -b 4 $(COMMON_TOKEN_OPTIONS) 

moritz_Lexer.cpp: moritz.qx A_B_C-token.cpp A_B_C-token_ids
	quex -i $< -o moritz::Lexer --icu -b 4 $(COMMON_TOKEN_OPTIONS) 

A_B_C-token_ids \
A_B_C-token.cpp: 
	quex -i token_ids.qx               \
		 --icu -b 4                    \
		 --token-id-prefix TKN_        \
		 -o A::B::C                    \
		 --token-class A::B::C::Token   \
		 --token-class-only 

clean:
	rm -rf $(ENGINE)
	rm -rf $(ENGINE:.cpp=.o)
	rm -rf $(ENGINE:.cpp=)
	rm -rf $(ENGINE:.cpp=-token_ids)
	rm -rf $(ENGINE:.cpp=-token)
	rm -rf $(ENGINE:.cpp=-configuration)
	rm -rf A_B_C-token*
	rm -rf lexer
	rm -rf *.E
	rm -rf lexer.o
