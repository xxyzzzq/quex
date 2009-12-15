all: iso8859-7-lexer utf8-lexer 


iso8859-7-lexer: iso8859-7-lexer.cpp
	quex -i greek.qx         \
		 --codec iso8859_7   \
		 --token-prefix TKN_ \
		 -o ISO8859_7_Lex
	g++ -ggdb -D__QUEX_TEST_OPTION_ISO8859_7           \
		-DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED \
		-Wall              \
		-I$(QUEX_PATH) -I. \
		$<                 \
		ISO8859_7_Lex.cpp  \
		ISO8859_7_Lex-core-engine.cpp \
		-o $@

utf8-lexer: utf8-lexer.cpp 
	quex -i greek.qx         \
		 --codec utf8        \
		 --token-prefix TKN_ \
		 -o UTF8Lex 
	g++ -ggdb \
		-DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED \
		-Wall                   \
		-I$(QUEX_PATH) -I.      \
		$<                      \
		UTF8Lex.cpp             \
		UTF8Lex-core-engine.cpp \
		-o $@

utf16-lexer: utf16-lexer.cpp 
	quex -i             greeky.qx  \
		 --codec        utf16     \
		 --token-prefix TKN_      \
		 -o             UTF16Lex  \
	     -b             2
	g++ -ggdb -D__QUEX_TEST_OPTION_UTF16BE             \
		-DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED \
		-Wall                   \
		-I$(QUEX_PATH) -I.      \
		$<                      \
		UTF16Lex.cpp             \
		UTF16Lex-core-engine.cpp \
		-o $@

			
%.E: %.cpp
	g++ -E -D__QUEX_TEST_OPTION_ISO8859_7 \
		-DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED \
		-Wall \
		-I$(QUEX_PATH) -I. \
		$< -o $@

clean:
	rm -f ISO8859_7_Lex*
	rm -f ISO8859_7_Lex-converter-iso8859_7
	rm -f iso8859-7-lexer
	rm -f UTF8Lex*
	rm -f utf8-lexer
	rm -f UTF16Lex*
	rm -f utf16-lexer
	rm -f *.E
	rm -f *.svg
