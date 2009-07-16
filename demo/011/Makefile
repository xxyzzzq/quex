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
		-o lexer

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
