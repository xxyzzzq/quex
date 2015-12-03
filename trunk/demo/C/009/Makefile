.PHONY: clean

ifndef QUEX_PATH
    $(error The environment variable QUEX_PATH is not defined!)
endif

FILES := lexer-command-line \
	     lexer-stdin  lexer-stdin-utf8  \
	     lexer-socket lexer-socket-utf8 \
	     feed-socket

# (*) COMPILER SETTINGS ________________________________________________________
#     (change COMPILER to whatever you use as compiler on the command line,
#      e.g. "make COMPILER=icpc" will use intel's c++ compiler)
ifdef ASSERTS_ENABLED_F
	CCFLAG_ASSERTS=# By default asserts are enabled
else 
	CCFLAG_ASSERTS=-DQUEX_OPTION_ASSERTS_DISABLED
endif

COMPILER := gcc -ggdb -Wall -Werror -pedantic 
CC       := $(COMPILER) -I./ -I$(QUEX_PATH) $(CCFLAG_ASSERTS) \
            -DQUEX_OPTION_POSIX 

# Debugging Options:
#   -DQUEX_OPTION_DEBUG_SHOW
#   -DQUEX_OPTION_ASSERTS_DISABLED
#   -DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED 
		 
LD = $(COMPILER) 

# (*) RULES ____________________________________________________________________
all: $(FILES)

# -- char application
lexer-socket:            lexer-socket.o LexAscii.o 
	$(LD) -o $@  $^                  

lexer-socket-utf8:       lexer-socket-utf8.o LexUtf8.o 
	$(LD) -o $@  $^                  

lexer-stdin:             lexer-stdin.o LexAscii.o
	$(LD) -o $@  $^

lexer-stdin-utf8:        lexer-stdin-utf8.o LexUtf8.o
	$(LD) -o $@  $^
          
lexer-command-line:      lexer-command-line.o LexAscii.o
	$(LD) -o $@  $^

lexer-command-line-utf8: lexer-command-line-utf8.o LexUtf8.o
	$(LD) -o $@  $^
          
feed-socket:             feed-socket.o
	$(LD) -o $@  $^                  
                                     
%.o: %.c LexAscii.h
	$(CC) -c $< -o $@ 

%-utf8.o: %.c LexUtf8.h
	$(CC) -DWITH_UTF8 -c $< -o $@ 

LexUtf8.h \
LexUtf8.c: utf8.qx 
	quex -i             utf8.qx \
	     -o             LexUtf8 \
		 --iconv                \
		 --language     C       \
		 --bet          wchar_t \
		 --token-policy single       
	
LexAscii.h \
LexAscii.c: ascii.qx 
	quex -i             ascii.qx \
		 -o             LexAscii \
	     --language     C        \
		 --token-policy single

# (*) HELPERS __________________________________________________________________
clean:	
	rm -f Lex*
	rm -f $(FILES)
	rm -f *.o
	rm -f *.bak
	rm -f *~
