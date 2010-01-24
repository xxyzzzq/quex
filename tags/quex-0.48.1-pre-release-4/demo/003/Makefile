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
COMPILER = g++

CC = $(COMPILER) -c -fPIC -Wno-deprecated -Wall \
	 -I./ -I$(QUEX_PATH) $(NDEBUG_F) \
	 -D___QUEX_UNIT_TESTING___ -ggdb \
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
MODE_FILES       = definitions.qx end_of_file.qx program.qx
# -- FILES PRODUCED BY QUEX
ENGINE_NAME      = tiny_lexer# NOTE: a whitespace after this name creates chaos!
ENGINE_SOURCES   = $(ENGINE_NAME)                     \
                   $(ENGINE_NAME).cpp                 \
                   $(ENGINE_NAME)-token_ids           \
                   $(ENGINE_NAME)-configuration       
# -- OUTPUT
OBJS        = $(APPLICATION).o \
			  $(ENGINE_NAME).o 
APPLICATION = lexer

# (*) RULES ____________________________________________________________________
# -- application
$(APPLICATION): $(OBJS)
	$(LD) $(OBJS) -o $(APPLICATION) 

# -- engine and object files
%.o: %.cpp $(ENGINE_SOURCES)
	$(CC) $< -o $@

$(ENGINE_SOURCES): $(MODE_FILES) $(QUEX_CORE)
	echo ":$(CONVERTER):" $(QUEX_FLAG)
	quex -i                         $(MODE_FILES)          \
		 --engine                   $(ENGINE_NAME)         \
	     --bytes-per-ucs-code-point $(BYTES_PER_CHARACTER) \
	     $(QUEX_FLAG)

# (*) HELPERS __________________________________________________________________
clean:	
	touch $(MODE_FILES)
	rm -f $(ENGINE_SOURCES)
	rm -f $(ENGINE_NAME)-token
	rm -f $(ENGINE_NAME).o
	rm -f lexer.o
	rm -f lexer
	rm -f token_ids
	rm -f *.bak
