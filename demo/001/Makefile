# PURPOSE: Makefile for unit tests.
#
# ABSOLUTELY NO WARRANTY
#_______________________________________________________________________________


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
GENERATED_MODE_FILES = \
		       $(ENGINE_NAME)-core-engine.cpp   \

GENERATED_MODE_OBJS  = $(GENERATED_MODE_FILES:.cpp=.o)
#
ENGINE_SOURCES   = $(ENGINE_NAME)                     \
                   $(ENGINE_NAME).cpp                 \
                   $(ENGINE_NAME)-token_ids           \
		   $(GENERATED_MODE_FILES)
#
LIBRARY_OBJS     = $(ENGINE_NAME).o


# (*) COMPILER SETTINGS ________________________________________________________
#
# -- compiler
CC = g++ -c -fPIC -Wno-deprecated -Wall \
	 -I./  -I$(QUEX_PATH) \
	 -D___QUEX_UNIT_TESTING___ -ggdb

# -- linker
LD         = g++ -ggdb
STATIC_LD  = ar -rv
DYNAMIC_LD = g++ -shared 


# (*) RULES ____________________________________________________________________
#
# -- application
$(APPLICATION_NAME): ./$(APPLICATION_NAME).o $(ENGINE_NAME).o $(GENERATED_MODE_OBJS)
	$(LD) ./$(APPLICATION_NAME).o $(ENGINE_NAME).o   \
	       $(GENERATED_MODE_OBJS)                    \
               -o $(APPLICATION_NAME) 

# -- libraries
$(LIBRARY_NAME).a:
	$(STATIC_LD) $@ $(LIBRARY_OBJS)

$(LIBRARY_NAME).so:
	$(DYNAMIC_LD) $(LIBRARY_OBJS) -o $@ 

# -- engine and object files
$(APPLICATION_NAME).o: $(APPLICATION_NAME).cpp $(ENGINE_SOURCES)
#       # require: $(ENGINE_SOURCES) for header files
	$(CC)    $(APPLICATION_NAME).cpp  \
              -o $(APPLICATION_NAME).o

$(ENGINE_NAME).o: $(ENGINE_SOURCES)
	$(CC)    $(ENGINE_NAME).cpp       \
              -o $(ENGINE_NAME).o

%.o: %.cpp
	$(CC) $< -o $@

$(ENGINE_SOURCES): $(MODE_FILES)
	quex --mode-files $(MODE_FILES)    \
	     --engine     $(ENGINE_NAME) 

# (*) HELPERS __________________________________________________________________
#
clean:	
	touch $(MODE_FILES)
	rm -f $(ENGINE_NAME) $(ENGINE_NAME).cpp \
              $(ENGINE_NAME)-internal.h $(ENGINE_NAME)-token_ids
	rm -f $(GENERATED_MODE_FILES)
	rm -f $(GENERATED_MODE_OBJS)
	rm -f $(ENGINE_NAME).o
	rm -f $(LIBRARY_NAME).a $(LIBRARY_NAME).so
	rm -f lexer.o
	rm -f lexer
	rm -f gmon.out
	rm -f token_ids
	rm -f *.bak

