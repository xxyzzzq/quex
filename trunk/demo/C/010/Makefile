# PURPOSE: Makefile building example applications for manual buffer filling.
#
# ABSOLUTELY NO WARRANTY
#_______________________________________________________________________________
.PHONY: clean UTF8 NON_UTF8

FILES := lexer.exe \
         lexer_utf8.exe \
         point.exe

ifndef QUEX_PATH
    $(error The environment variable QUEX_PATH is not defined!)
endif

# (*) SETUP ____________________________________________________________________
OBJS      := lexPlain.o receiver.o
UTF8_OBJS := lexUTF8.o  receiver_utf8.o

# (*) COMPILER SETTINGS ________________________________________________________
#     (change COMPILER to whatever you use as compiler on the command line,
#      e.g. "make COMPILER=icpc" will use intel's c++ compiler)
ifdef ASSERTS_ENABLED_F
	CCFLAG_ASSERTS=# By default asserts are enabled
else 
	CCFLAG_ASSERTS=-DQUEX_OPTION_ASSERTS_DISABLED
endif

COMPILER := gcc -ggdb -Wall -Werror -pedantic -std=c89

CC       := $(COMPILER) -I./ -I$(QUEX_PATH) $(CCFLAG_ASSERTS) 
            # -DQUEX_OPTION_DEBUG_SHOW    
            # -DQUEX_OPTION_ASSERTS_DISABLED
   	        # -DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED

CC_UTF8  := $(CC) -DQUEX_TYPE_CHARACTER=wchar_t \
				  -DQUEX_EXAMPLE_WITH_CONVERTER

# (*) RULES ____________________________________________________________________
all: $(FILES)

lexer.exe:           lexer.o $(OBJS)  
	$(CC) -o $@ $< $(OBJS) 
          
lexer_utf8.exe:      lexer_utf8.o $(UTF8_OBJS)  
	$(CC_UTF8) -o $@ $< $(UTF8_OBJS) 

point.exe:           point.c $(OBJS)  
	## All related files must be compiled with fallback_n = 0 
	$(CC)      -o $@ -DQUEX_SETTING_BUFFER_MIN_FALLBACK_N=0 $< $(OBJS) 
          
%.o:                 %.c  lexPlain.h
	$(CC)      -c $< -o $@  
          
%_utf8.o:            %.c  lexUTF8.h
	$(CC_UTF8) -c $< -o $@ 
          
%.E:                 %.c  
	$(CC)      -E $< -o $@  
          
lexPlain.h lexPlain.c: lexPlain.qx 
	quex -i             lexPlain.qx  \
		 -o             lexPlain     \
		 --token-policy single       \
		 --language     C            \
		 --token-memory-management-by-user 

lexUTF8.h lexUTF8.c: lexUTF8.qx 
	quex -i                    lexUTF8.qx   \
		 -o                    lexUTF8      \
		 --iconv                            \
		 --token-policy        single       \
		 --language            C            \
		 --buffer-element-type wchar_t      \
		 --token-memory-management-by-user

# (*) HELPERS __________________________________________________________________
clean:	
	touch simple.qx
	rm -f lexPlain.[ch] lexPlain-configuration.h lexPlain-token.h lexPlain-token_ids.h
	rm -f lexUTF8.[ch]  lexUTF8-configuration.h  lexUTF8-token.h  lexUTF8-token_ids.h
	rm -f $(FILES)
	rm -f *.exe
	rm -f *.o
	rm -f *.E
	rm -f *.bak
	rm -f tmp*
	rm -f *~
