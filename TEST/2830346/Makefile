ENGINE = \
		boeck_Lexer.cpp              \
		boeck_Lexer-core-engine.cpp  \
		max_Lexer.cpp                \
		max_Lexer-core-engine.cpp    \
		moritz_Lexer.cpp             \
		moritz_Lexer-core-engine.cpp \

story: boeck_Lexer.cpp max_Lexer.cpp moritz_Lexer.cpp
	g++ -ggdb lexer.cpp $(ENGINE) -o  $@ \
		-I$(QUEX_PATH) \
		-DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED 

story.E:
	g++ -E lexer.cpp $(ENGINE) -o  $@ \
		-I$(QUEX_PATH) \
		-DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED 

boeck_Lexer.cpp boeck_Lexer-core-engine.cpp: boeck.qx
	quex -i token.qx $< -o boeck::Lexer --codec utf8 --token-prefix TKN_ --token-policy users_token

max_Lexer.cpp max_Lexer-core-engine.cpp: max.qx
	quex -i token.qx $< -o max::Lexer --codec utf8 --token-prefix MAX_TKN_ --token-policy users_token

moritz_Lexer.cpp moritz_Lexer-core-engine.cpp: moritz.qx
	quex -i token.qx $< -o moritz::Lexer --codec utf8 --token-prefix MORITZ_TKN_ --token-policy users_token

clean:
	rm -rf $(ENGINE)
	rm -rf $(ENGINE:.cpp=.o)
	rm -rf $(ENGINE:.cpp=)
	rm -rf $(ENGINE:.cpp=-token_ids)
	rm -rf $(ENGINE:.cpp=-configuration)
	rm -rf story
	rm -rf story.E
