ENGINE = \
		boeck_Lexer.cpp              \
		boeck_Lexer-core-engine.cpp  \
		max_Lexer.cpp                \
		max_Lexer-core-engine.cpp    \
		moritz_Lexer.cpp             \
		moritz_Lexer-core-engine.cpp \

OBJS = $(ENGINE:.cpp=.o) lexer.o


lexer: $(OBJS)
	g++ $(OBJS) -ggdb -o  $@ \
		-I$(QUEX_PATH) \
		-DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED 

%.o: %.cpp $(ENGINE_SOURCES)
	g++ -c $< -ggdb -Wall -o $@ \
		-I$(QUEX_PATH) \
		$(NDEBUG_F) \
		-DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED 

%.E: %.cpp
	g++ -E $< -o  $@ \
		-I$(QUEX_PATH) \
		-DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED 

max_Lexer.cpp max_Lexer-core-engine.cpp: max.qx
	quex -i token.qx $< -o max::Lexer --iconv -b 4 --token-prefix MAX_TKN_ --token-policy users_token

moritz_Lexer.cpp moritz_Lexer-core-engine.cpp: moritz.qx
	quex -i token.qx $< -o moritz::Lexer --iconv -b 2 --token-prefix MORITZ_TKN_ --token-policy users_token

boeck_Lexer.cpp boeck_Lexer-core-engine.cpp: boeck.qx
	quex -i token.qx $< -o boeck::Lexer --codec utf8 --token-prefix TKN_ --token-policy users_token

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
