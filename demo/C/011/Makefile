
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

CC := gcc -ggdb -Wall -Werror -I$(QUEX_PATH) -I. $(CCFLAG_ASSERTS)

all: $(APPS)

iso8859-7-lexer: iso8859-7-lexer.c greek.qx
	quex -i                greek.qx  \
		 --language        C         \
		 --codec           iso8859_7 \
		 --token-id-prefix TKN_      \
		 -o                ISO8859_7_Lex 
	$(CC) -D__QUEX_TEST_OPTION_ISO8859_7 $< ISO8859_7_Lex.c -o $@

utf8-lexer: utf8-lexer.c greek.qx
	quex -i greek.qx            \
		 --language        C    \
		 --codec utf8           \
		 --token-id-prefix TKN_ \
		 -o UTF8Lex 
	$(CC) $< UTF8Lex.c -o $@
	
utf16-lexer: utf16-lexer.c greek.qx
	quex -i                greek.qx  \
		 --language        C         \
		 --codec           utf16     \
		 --token-id-prefix TKN_      \
		 -o                UTF16Lex  \
	     -b                2
	$(CC) -D__QUEX_TEST_OPTION_UTF16BE $< UTF16Lex.c -o $@

utf16-lexer-other: utf16-lexer-other.c greek-other.qx
	quex -i                greek-other.qx  \
		 --language        C               \
		 --codec           utf16           \
		 --token-id-prefix TKN_            \
		 -o                UTF16Lex        \
	     -b                2
	$(CC) -D__QUEX_TEST_OPTION_UTF16BE $< UTF16Lex.c -o $@

%.E: %.c
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

