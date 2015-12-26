# PURPOSE: Makefile for Demo Application of Quex
# 
# USAGES:
# 
#     make lexer CONVERTER=iconv   
#
#         creates a lexer using the iconv library. This is actually the
#         default which is done even if no 'CONVERTER' is specified.
#
#     make lexer CONVERTER=icu   
#
#         creates a lexer using the icu library.
#
# ABSOLUTELY NO WARRANTY
#_______________________________________________________________________________
.PHONY: clean

ifndef QUEX_PATH
    $(error The environment variable QUEX_PATH is not defined!)
endif

ifndef BYTES_PER_CHARACTER
    BYTES_PER_CHARACTER = 2
endif


ifdef ASSERTS_ENABLED_F
	CCFLAG_ASSERTS=# By default asserts are enabled
else 
	CCFLAG_ASSERTS=-DQUEX_OPTION_ASSERTS_DISABLED
endif

# (*) COMPILER SETTINGS ________________________________________________________
#     (change COMPILER to whatever you use as compiler on the command line,
#      e.g. "make COMPILER=icpc" will use intel's c++ compiler)
COMPILER = gcc -ggdb -W -pedantic

CC = $(COMPILER) -c \
	 -I./ -I$(QUEX_PATH)                             \
	 -Wall -Werror -Wconversion                      \
	 $(CCFLAG_ASSERTS)                               \
	 -DENCODING_NAME='"UTF8"'                        \
	 -DPRINT_TOKEN         
	 # -DQUEX_OPTION_ASSERTS_DISABLED
	 # -DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED \
     # -DQUEX_OPTION_DEBUG_SHOW
   
LD = $(COMPILER) 

# (*) Determining the Converter Lib (IConv or ICU) ____________________________
#
# Some compiler distributions have iconv in a separate lib:
#    -- Intel's icpc (tm)
#    -- MS's cl (tm)
#    -- Digital Mars dmc (tm)
#    -- g++ on apple (tm)
ifneq (,$(or $(findstring apple, $(shell $(COMPILER) --version)), \
             $(findstring $(COMPILER),icpc cl dmc)))
	LIBICONV=-liconv
else
    LIBICONV=#
endif

CONVERTER=undefined # (overidden by command line specification)
ifeq ($(CONVERTER),icu)
	LIB_CONV  = `icu-config --ldflags`
	QUEX_FLAG = --icu
else
	LIB_CONV  = $(LIBICONV)
	QUEX_FLAG = --iconv
endif


# (*) RULES ____________________________________________________________________
# -- application
lexer:          example.o EasyLexer.o
	$(LD) -o $@ example.o EasyLexer.o $(LIB_CONV) 
          
lexer-with-bom: lexer-with-bom.o EasyLexer.o
	$(LD) -o $@ lexer-with-bom.o EasyLexer.o $(LIB_CONV) 
          
# Object files:
EasyLexer.o: EasyLexer.c 
	$(CC) $< -o $@ 

example.o: ../example.c  EasyLexer.c
	$(CC) $< -o $@ 

lexer-with-bom.o: lexer-with-bom.c EasyLexer.c
	$(CC) $< -o $@ 

# Macro expansions (only for debugging):
%.E: %.c    
	$(CC) -E $< -o $@ 

EasyLexer.c: definitions.qx end_of_file.qx program.qx 
	quex -i                definitions.qx end_of_file.qx program.qx \
	     -o                EasyLexer              \
		 --token-id-offset 0x1000                 \
	     -b                $(BYTES_PER_CHARACTER) \
		 --language        C                      \
		 $(QUEX_FLAG)

# (*) HELPERS __________________________________________________________________
clean:	
	rm -f EasyLexer*
	rm -f *.o
	rm -f *.bak
	rm -f *.E
	rm -f lexer lexer-with-bom
