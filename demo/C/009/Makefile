# PURPOSE: Makefile Demo Application of Quex
#
# ABSOLUTELY NO WARRANTY
#_______________________________________________________________________________
.PHONY: clean

ifndef QUEX_PATH
    $(error The environment variable QUEX_PATH is not defined!)
endif

ALL_ENGINES := LexAscii.c LexUtf8WChar.c LexUtf8Uint32.c
FILES       := lexer-command-line \
	           lexer-stdin  lexer-stdin-utf8  \
	           lexer-socket lexer-socket-utf8 \
	           lexer-pipe   lexer-pipe-utf8   \
			   feed-socket

# (*) COMPILER SETTINGS ________________________________________________________
#     (change COMPILER to whatever you use as compiler on the command line,
#      e.g. "make COMPILER=icpc" will use intel's c++ compiler)
ifdef ASSERTS_ENABLED_F
	CCFLAG_ASSERTS=# By default asserts are enabled
else 
	CCFLAG_ASSERTS=-DQUEX_OPTION_ASSERTS_DISABLED
endif

COMPILER = gcc -ggdb -Wall -Werror -pedantic 
CC = $(COMPILER) -I./ -I$(QUEX_PATH) $(CCFLAG_ASSERTS) \
	 -DQUEX_OPTION_POSIX 

# Debugging Options:
#   -DQUEX_OPTION_DEBUG_SHOW
#   -DQUEX_OPTION_ASSERTS_DISABLED
#   -DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED 
		 
LD = $(COMPILER) 

# (*) RULES ____________________________________________________________________
all: $(FILES)

# -- char application
lexer-socket:     lexer-socket.o     LexAscii.o 
	$(LD) -o $@  $^                  

feed-socket:      feed-socket.o
	$(LD) -o $@  $^                  
                                     
lexer-stdin:      lexer-stdin.o      LexAscii.o
	$(LD) -o $@  $^

lexer-stdin-utf8: lexer-stdin-utf8.o LexUtf8Uint32.o
	$(LD) -o $@  $^
          
%.o: %.c $(ALL_ENGINES)
	$(CC) -c $< -o $@ 

LexUtf8WChar.c: utf8.qx 
	quex -i             utf8.qx      \
	     -o             LexUtf8WChar \
		 --language     C            \
		 --bet          wchar_t      \
		 --token-policy single       
	
LexUtf8Uint32.c: utf8.qx 
	quex -i             utf8.qx       \
	     -o             LexUtf8Uint32 \
		 --language     C             \
		 --bet          uint32_t      \
		 --token-policy single       
	
LexAscii.c: ascii.qx 
	quex -i ascii.qx -o LexAscii --language C \
		 --token-policy single

# (*) HELPERS __________________________________________________________________
clean:	
	rm -f Lex*
	rm -f $(FILES)
	rm -f *.o
	rm -f *.bak
	rm -f *~
