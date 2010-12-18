# PURPOSE: Makefile Demo Application of Quex
#
# ABSOLUTELY NO WARRANTY
#_______________________________________________________________________________
.PHONY: clean

FILES = copy.exe    fill.exe    point.exe \
		copy-ez.exe fill-ez.exe re-point.exe

ifndef QUEX_PATH
    $(error The environment variable QUEX_PATH is not defined!)
endif

include $(QUEX_PATH)/quex/code_base/core.mkd

# (*) SETUP ____________________________________________________________________
OBJS      = tiny_lexer.o      messaging-framework.o
SRCS      = $(OBJS:.o=.c)
UTF8_OBJS = tiny_lexer-utf8.o messaging-framework-utf8.o

# (*) COMPILER SETTINGS ________________________________________________________
#     (change COMPILER to whatever you use as compiler on the command line,
#      e.g. "make COMPILER=icpc" will use intel's c++ compiler)
ifdef ASSERTS_ENABLED_F
	CCFLAG_ASSERTS=# By default asserts are enabled
else 
	CCFLAG_ASSERTS=-DQUEX_OPTION_ASSERTS_DISABLED
endif

# Use 'C99' to avoid line number limit of 32767 in '#line' pragma
COMPILER = gcc -ggdb -Wall -pedantic -std=c99

CC = $(COMPILER) -I./ -I$(QUEX_PATH) $(CCFLAG_ASSERTS) \
     # -DQUEX_OPTION_ASSERTS_DISABLED
	 # -DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED
     # -D__QUEX_OPTION_DEBUG_STATE_TRANSITION_REPORTS \

CC_UTF8 = $(CC) -D__QUEX_OPTION_MESSAGE_UTF8 \
		        -DQUEX_TYPE_CHARACTER=wchar_t \
		        -DQUEX_OPTION_CONVERTER_ICONV 

# (*) RULES ____________________________________________________________________
all: $(FILES)

# -- char application
          
%-conversion-direct.exe: %-conversion-direct.c $(UTF8_OBJS) $(QUEX_CORE) 
	$(CC_UTF8) -o $@ $< $(UTF8_OBJS) 

%-conversion.exe:        %-conversion.c $(UTF8_OBJS) $(QUEX_CORE) 
	$(CC_UTF8) -o $@ $< $(UTF8_OBJS) 
          
%.exe:                   %.c $(OBJS) $(QUEX_CORE) 
	$(CC)      -o $@ $< $(OBJS) 

point.exe:               point.c $(SRCS) $(QUEX_CORE) 
	$(CC)      -o $@ -DQUEX_SETTING_BUFFER_MIN_FALLBACK_N=0 $< $(SRCS) 
          
re-point.exe:            re-point.c $(SRCS) $(QUEX_CORE) 
	$(CC)      -o $@ -DQUEX_SETTING_BUFFER_MIN_FALLBACK_N=0 $< $(SRCS) 
          
%-utf8.o:                %.c $(QUEX_CORE) tiny_lexer
	$(CC_UTF8) -c $< -o $@  
          
%.o:                     %.c $(QUEX_CORE) tiny_lexer
	$(CC)      -c $< -o $@  
          
%.E:                     %.c $(QUEX_CORE) tiny_lexer
	$(CC)      -E $< -o $@  
          
tiny_lexer tiny_lexer.c: simple.qx $(QUEX_CORE)
	# Don't need to set '--iconv'. The flag 'QUEX_OPTION_CONVERTER_ICONV'
	# does all what is required.
	quex -i simple.qx --engine tiny_lexer \
		 --token-policy single \
		 --language C          \
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
