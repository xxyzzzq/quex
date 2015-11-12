# PURPOSE: Makefile building example applications for manual buffer filling.
#
# ABSOLUTELY NO WARRANTY
#_______________________________________________________________________________
.PHONY: clean UTF8 NON_UTF8

FILES := lexer.exe \
         lexer-converter.exe \
         re-point.exe

ifndef QUEX_PATH
    $(error The environment variable QUEX_PATH is not defined!)
endif

# (*) SETUP ____________________________________________________________________
OBJS      := tiny_lexer.o      messaging_framework.o
UTF8_OBJS := tiny_lexer_utf8.o messaging_framework_utf8.o

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

CC_UTF8  := $(CC) -D__QUEX_OPTION_MESSAGE_UTF8 \
                  -DQUEX_TYPE_CHARACTER=wchar_t 

# (*) RULES ____________________________________________________________________
all: $(FILES)

lexer.exe:           lexer.o $(OBJS)  
	$(CC) -o $@ $< $(OBJS) 
          
lexer_utf8.exe: lexer_utf8.o $(UTF8_OBJS)  
	$(CC_UTF8) -o $@ $< $(UTF8_OBJS) 

point.exe:           point.c $(OBJS:.o=.c)  NON_UTF8
	## All related files must be compiled with fallback_n = 0 
	$(CC)      -o $@ -DQUEX_SETTING_BUFFER_MIN_FALLBACK_N=0 $< $(OBJS:.o=.c) 
          
re-point.exe:        re-point.c  $(OBJS:.o=.c) NON_UTF8
	## All related files must be compiled with fallback_n = 0
	$(CC)      -o $@ -DQUEX_SETTING_BUFFER_MIN_FALLBACK_N=0 $< $(OBJS:.o=.c) 
          
%_utf8.o:            %.c  UTF8
	$(CC_UTF8) -c $< -o $@ 
          
%.o:                 %.c  NON_UTF8
	$(CC)      -c $< -o $@  
          
%.E:                 %.c  NON_UTF8
	$(CC)      -E $< -o $@  
          
tiny_lexer.h tiny_lexer.c:            NON_UTF8

tiny_lexer_utf8.h tiny_lexer_utf8.c:  UTF8

NON_UTF8: simple.qx 
	quex -i             simple.qx          \
		 -o             tiny_lexer         \
		 --token-policy single             \
		 --language     C                  \
		 --token-memory-management-by-user 

UTF8: simple_utf8.qx 
	quex -i                    simple_utf8.qx   \
		 -o                    tiny_lexer_utf8  \
		 --iconv                                \
		 --token-policy        single           \
		 --language            C                \
		 --buffer-element-type wchar_t          \
		 --token-memory-management-by-user

# (*) HELPERS __________________________________________________________________
clean:	
	touch simple.qx
	rm -f tiny_lexer*
	rm -f $(SOURCES)
	rm -f tiny_lexer-configuration
	rm -f $(FILES)
	rm -f *.exe
	rm -f *.o
	rm -f *.E
	rm -f copy fill point
	rm -f *.bak
	rm -f tmp*
