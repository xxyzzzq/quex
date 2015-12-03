# See README.txt
# (C) Frank-Rene Schaefer
#______________________________________________________________________________
.PHONY: clean

FILES := lexer-command-line lexer-command-line-utf8 \
	     lexer-stdin        lexer-stdin-utf8        \
	     lexer-socket       lexer-socket-utf8       \
	     feed-socket

# (*) COMPILER SETTINGS ________________________________________________________
#
ifndef QUEX_PATH
    $(error The environment variable QUEX_PATH is not defined!)
endif

ifdef ASSERTS_ENABLED_F
	ASSERTS :=# By default asserts are enabled
else 
	ASSERTS :=-DQUEX_OPTION_ASSERTS_DISABLED
endif

COMPILER := g++ -ggdb -Wall -Werror -pedantic 
CC       := $(COMPILER) -I./ -I$(QUEX_PATH) $(ASSERTS) \
            -DQUEX_OPTION_POSIX 
LD       := $(COMPILER) 

# Debugging Options:  -DQUEX_OPTION_DEBUG_SHOW
#                     -DQUEX_OPTION_ASSERTS_DISABLED
#                     -DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED 
		 

# (*) RULES ____________________________________________________________________
all: $(FILES)

lexer-socket:            lexer-socket.o            LexAscii.o 
	$(LD) -o $@  $^                  

lexer-socket-utf8:       lexer-socket-utf8.o       LexUtf8.o 
	$(LD) -o $@  $^                  

lexer-stdin:             lexer-stdin.o             LexAscii.o
	$(LD) -o $@  $^

lexer-stdin-utf8:        lexer-stdin-utf8.o        LexUtf8.o
	$(LD) -o $@  $^
          
lexer-command-line:      lexer-command-line.o      LexAscii.o
	$(LD) -o $@  $^

lexer-command-line-utf8: lexer-command-line-utf8.o LexUtf8.o
	$(LD) -o $@  $^
          
feed-socket:             feed-socket.o
	$(LD) -o $@  $^                  
                                     
%.o: %.cpp LexAscii
	$(CC) -c $< -o $@ 

%-utf8.o: %.cpp LexUtf8
	$(CC) -DWITH_UTF8 -c $< -o $@ 

LexUtf8 LexUtf8.cpp: utf8.qx 
	quex -i             utf8.qx \
	     -o             LexUtf8 \
		 --iconv                \
		 --bet          wchar_t \
		 --token-policy single       
	
LexAscii LexAscii.cpp: ascii.qx 
	quex -i             ascii.qx \
		 -o             LexAscii \
		 --token-policy single

# (*) HELPERS __________________________________________________________________
clean:	
	rm -f Lex*
	rm -f $(FILES)
	rm -f *.o
	rm -f *.bak
	rm -f *~
