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
#
# ABSOLUTELY NO WARRANTY
#_______________________________________________________________________________
include $(QUEX_PATH)/quex/code_base/core.mkd
.PHONY: clean

ifndef QUEX_PATH
    $(error The environment variable QUEX_PATH is not defined!)
endif

ifndef BYTES_PER_CHARACTER
    BYTES_PER_CHARACTER = 2
endif

# (*) COMPILER SETTINGS ________________________________________________________
#     (change COMPILER to whatever you use as compiler on the command line,
#     e.g. "make COMPILER=icpc" will use intel's c++ compiler)
COMPILER = gcc

CC = $(COMPILER) -c -fPIC -Wall -Wimplicit -pedantic\
	 -I./ -I$(QUEX_PATH) $(NDEBUG_F) \
	 -ggdb \
	 -DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED

LD = $(COMPILER) $(LIB_CONV) 

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


# (*) SETUP ____________________________________________________________________
# -- INPUT
MODE_FILES  = definitions.qx \
			  end_of_file.qx \
			  program.qx
# -- FILES PRODUCED BY QUEX
ENGINE_NAME = tiny_lexer# NOTE: a whitespace after this name creates chaos!

# -- OUTPUT
OBJS = lexer.o $(ENGINE_NAME).o 

# (*) RULES ____________________________________________________________________
# -- application
lexer: $(OBJS)
	$(LD) $(OBJS) -o lexer

# -- engine and object files (make sure that code has been generated)
%.o: %.c tiny_lexer.c
	$(CC) $< -o $@

%.o: %.E 
	$(CC:-c=-E) $< -o $@

tiny_lexer.c: $(MODE_FILES) $(QUEX_CORE)
	@echo ":$(CONVERTER):" $(QUEX_FLAG)
	quex -i                         $(MODE_FILES)          \
		 --engine                   $(ENGINE_NAME)         \
	     --bytes-per-ucs-code-point $(BYTES_PER_CHARACTER) \
		 --language C                                      \
	     $(QUEX_FLAG)

# (*) HELPERS __________________________________________________________________
clean:	
	touch $(MODE_FILES)
	rm -f tiny_lexer*
	rm -f $(ENGINE_NAME)-*
	rm -f $(ENGINE_NAME).[oE]
	rm -f lexer.[oE]
	rm -f lexer
	rm -f *.bak
