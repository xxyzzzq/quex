GENERATED = ISO8859_7_Lexer.cpp \
            ISO8859_7_Lexer-core-engine.cpp 

greek-lexer: 
	quex -i greek.qx \
		 --codec iso8859_7 \
		 --token-prefix TKN_ \
		 -o ISO8859_7_Lexer 
	g++ -ggdb -D__QUEX_TEST_OPTION_ISO8859_7 \
		-DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED \
		-Wall \
		-I$(QUEX_PATH) -I. \
		lexer.cpp \
		ISO8859_7_Lexer.cpp \
		ISO8859_7_Lexer-core-engine.cpp \
		-o $@

utf8-lexer: 
	quex -i greek.qx \
		 --codec utf8 \
		 --token-prefix TKN_ \
		 -o UTF8Lex 
	g++ -ggdb -D__QUEX_TEST_OPTION_ISO8859_7 \
		-DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED \
	    -D__QUEX_OPTION_DEBUG_STATE_TRANSITION_REPORTS \
		-Wall \
		-I$(QUEX_PATH) -I. \
		utf8-lexer.cpp \
		UTF8Lex.cpp \
		UTF8Lex-core-engine.cpp \
		-o $@

%.E: %.cpp
	g++ -E -D__QUEX_TEST_OPTION_ISO8859_7 \
		-DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED \
		-Wall \
		-I$(QUEX_PATH) -I. \
		$< -o $@

clean:
	rm -f lexer
	rm -f ISO8859_7_Lexer
	rm -f ISO8859_7_Lexer-core-engine.cpp      
	rm -f ISO8859_7_Lexer-token_ids
	rm -f ISO8859_7_Lexer-converter-iso8859_7  
	rm -f ISO8859_7_Lexer.cpp
