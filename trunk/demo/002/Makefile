# PURPOSE: Makefile for unit tests.
#
# ABSOLUTELY NO WARRANTY
#_______________________________________________________________________________
include $(QUEX_PATH)/quex/code_base/core.mkd

# (*) SETUP ____________________________________________________________________
#
# QUEX_PATH    = ../../ # there should be an environment variable 'QUEX_PATH'
#                       # thus this does have to be defined explicitly here.
#
# -- INPUT
MODE_FILES   = simple.qx
DEBUG_F      = # --debug # set flag if debugging info is required
#
# -- APPLICATION / LIBRARY specification
APPLICATION_NAME = lexer
LIBRARY_NAME     = libLexer
ENGINE_NAME      = tiny_lexer# NOTE: a whitespace after this name creates chaos!
#
ENGINE_SOURCES   = $(ENGINE_NAME)                     \
                   $(ENGINE_NAME).cpp                 \
                   $(ENGINE_NAME)-token_ids           \
                   $(ENGINE_NAME)-configuration       
#
LIBRARY_OBJS     = $(ENGINE_NAME).o


# (*) COMPILER SETTINGS ________________________________________________________
#     (change COMPILER to whatever you use as compiler on the command line,
#     e.g. "make COMPILER=icpc" will use intel's c++ compiler)
COMPILER = g++
# -- compiler
CC = $(COMPILER) -c -fPIC -ggdb -Wno-deprecated -Wall \
	 -I./ -I$(QUEX_PATH) $(NDEBUG_F)      \
	 -DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED
	 #-DQUEX_OPTION_DEBUG_MODE_TRANSITIONS \
	 #-D__QUEX_OPTION_DEBUG_STATE_TRANSITION_REPORTS

# -- linker
LD         = $(COMPILER) 

# (*) RULES ____________________________________________________________________
#
# -- application
$(APPLICATION_NAME): ./$(APPLICATION_NAME).o $(ENGINE_NAME).o 
	$(LD) ./$(APPLICATION_NAME).o $(ENGINE_NAME).o   \
          -o $(APPLICATION_NAME) 

# -- engine and object files
$(APPLICATION_NAME).o: $(APPLICATION_NAME).cpp $(ENGINE_SOURCES)
	$(CC) $(APPLICATION_NAME).cpp -o $(APPLICATION_NAME).o

$(ENGINE_NAME).o: $(ENGINE_SOURCES)
	$(CC) $(ENGINE_NAME).cpp -o $(ENGINE_NAME).o

%.o: %.cpp
	$(CC) $< -o $@

$(ENGINE_SOURCES): $(MODE_FILES) $(QUEX_CORE)
	quex --mode-files $(MODE_FILES)    \
	     --engine     $(ENGINE_NAME)   


# (*) HELPERS __________________________________________________________________
#
clean:	
	touch $(MODE_FILES)
	rm -f $(ENGINE_NAME) $(ENGINE_NAME).cpp \
          $(ENGINE_NAME)-internal.h \
		  $(ENGINE_NAME)-token \
		  $(ENGINE_NAME)-token_ids \
		  $(ENGINE_NAME)-configuration
	rm -f $(ENGINE_NAME).o
	rm -f $(LIBRARY_NAME).a $(LIBRARY_NAME).so
	rm -f lexer.o
	rm -f lexer
	rm -f gmon.out
	rm -f token_ids
	rm -f *.bak
