ENGINE = \
		boeck.cpp              \
		boeck-core-engine.cpp  \
		max.cpp                \
		max-core-engine.cpp    \
		moritz.cpp             \
		moritz-core-engine.cpp \

story: boeck.cpp max.cpp moritz.cpp
	g++ -ggdb lexer.cpp $(ENGINE) -o  story \
		-I$(QUEX_PATH) \
		-DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED 

boeck.cpp boeck-core-engine.cpp: boeck.qx
	quex -i token.qx $< -o boeck --codec utf8 --token-prefix TKN_ --token-policy users_token

max.cpp max-core-engine.cpp: max.qx
	quex -i token.qx $< -o max --codec utf8 --token-prefix MAX_TKN_ --token-policy users_token

moritz.cpp moritz-core-engine.cpp: moritz.qx
	quex -i token.qx $< -o moritz --codec utf8 --token-prefix MORITZ_TKN_ --token-policy users_token

clean:
	rm -rf $(ENGINE)
	rm -rf $(ENGINE:.cpp=.o)
	rm -rf $(ENGINE:.cpp=)
	rm -rf $(ENGINE:.cpp=-token_ids)
	rm -rf $(ENGINE:.cpp=-configuration)
	rm -rf story
