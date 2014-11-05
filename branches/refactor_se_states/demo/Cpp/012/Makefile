ENGINE = \
		boeck_Lexer.cpp              \
		max_Lexer.cpp                \
		moritz_Lexer.cpp             

OBJS =  lexer.o $(ENGINE:.cpp=.o)

ifdef ASSERTS_ENABLED_F
	CCFLAG_ASSERTS=# By default asserts are enabled
else 
	CCFLAG_ASSERTS=-DQUEX_OPTION_ASSERTS_DISABLED
endif

CC := g++ -ggdb -Wall -Werror -DQUEX_OPTION_MULTI 

lexer: $(OBJS)
	g++ $(OBJS) -ggdb -o $@ 
	 
# -DQUEX_OPTION_ASSERTS_DISABLED
# -DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED 
#
lexer.o: lexer.cpp $(ENGINE)
	$(CC) -c $< -o $@ -I$(QUEX_PATH) $(CCFLAG_ASSERTS) 

%.o: %.cpp 
	$(CC) -c $< -o $@ -I$(QUEX_PATH) $(CCFLAG_ASSERTS) 
	
# -DQUEX_OPTION_ASSERTS_DISABLED
# -DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED 

%.E: %.cpp
	g++ -E $< -o  $@ \
		-I$(QUEX_PATH) 
		
# -DQUEX_OPTION_ASSERTS_DISABLED
# -DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED 

max_Lexer.cpp:    max.qx
	quex -i token.qx $< -o max::Lexer --iconv -b 4     \
		 --token-id-prefix MAX_TKN_ --token-policy single \
		 --suppress 6

moritz_Lexer.cpp: moritz.qx
	quex -i token.qx $< -o moritz::Lexer --iconv -b 2     \
		 --token-id-prefix MORITZ_TKN_ --token-policy single \
		 --suppress 6

boeck_Lexer.cpp:  boeck.qx
	quex -i token.qx $< -o boeck::Lexer --codec utf8 \
		 --token-id-prefix TKN_ --token-policy single   \
		 --suppress 6

clean:
	rm -rf $(ENGINE)
	rm -rf $(ENGINE:.cpp=.o)
	rm -rf $(ENGINE:.cpp=)
	rm -rf $(ENGINE:.cpp=-token_ids)
	rm -rf $(ENGINE:.cpp=-token)
	rm -rf $(ENGINE:.cpp=-configuration)
	rm -rf lexer
	rm -rf *.E
	rm -rf lexer.o
