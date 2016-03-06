
APPS := iso8859-7-lexer \
	    utf8-lexer      \
		utf16-lexer     \
		utf16-lexer-other

ifdef ASSERTS_ENABLED_F
	CCFLAG_ASSERTS :=# By default asserts are enabled
else 
	CCFLAG_ASSERTS := -DQUEX_OPTION_ASSERTS_DISABLED
endif

# Other useful options:
#   -DQUEX_OPTION_ASSERTS_DISABLED
#   -DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED
#   -DQUEX_OPTION_DEBUG_SHOW 

CC := g++ -ggdb -Wall -Werror -I$(QUEX_PATH) -I. $(CCFLAG_ASSERTS)

all: $(APPS)

iso8859-7-lexer: iso8859-7-lexer.cpp greek.qx
	quex -i                greek.qx  \
		 --codec           iso8859_7 \
		 --token-id-prefix TKN_      \
		 -o                ISO8859_7_Lex 
	$(CC) -D__QUEX_TEST_OPTION_ISO8859_7 $< ISO8859_7_Lex.cpp -o $@

utf8-lexer: utf8-lexer.cpp greek.qx
	quex -i greek.qx         \
		 --codec utf8        \
		 --token-id-prefix TKN_ \
		 -o UTF8Lex 
	$(CC) $< UTF8Lex.cpp -o $@
	
utf16-lexer: utf16-lexer.cpp greek.qx
	quex -i                greek.qx  \
		 --codec           utf16     \
		 --token-id-prefix TKN_      \
		 -o                UTF16Lex  \
	     -b                2
	$(CC) -D__QUEX_TEST_OPTION_UTF16BE $< UTF16Lex.cpp -o $@

utf16-lexer-other: utf16-lexer-other.cpp greek-other.qx
	quex -i                greek-other.qx  \
		 --codec           utf16           \
		 --token-id-prefix TKN_            \
		 -o                UTF16Lex        \
	     -b                2
	$(CC) -D__QUEX_TEST_OPTION_UTF16BE $< UTF16Lex.cpp -o $@

%.E: %.cpp
	g++ -E -D__QUEX_TEST_OPTION_ISO8859_7 \
		-I$(QUEX_PATH) -I. $< -o $@
	
clean:
	rm -f ISO8859_7_Lex* UTF8Lex* UTF16Lex*
	rm -f $(APPS)
	rm -f *.E
	rm -f *.svg
	rm -f *.o
	rm -f *.bak
	rm -f tmp.*
	rm -f *~

