# PURPOSE: Makefile Demo Application of Quex
#
# ABSOLUTELY NO WARRANTY
#_______________________________________________________________________________
.PHONY: clean

FILES = copy.exe    fill.exe    point.exe \
		copy-ez.exe fill-ez.exe

ifndef QUEX_PATH
    $(error The environment variable QUEX_PATH is not defined!)
endif

include $(QUEX_PATH)/quex/code_base/core.mkd

# (*) SETUP ____________________________________________________________________
SOURCES   = tiny_lexer.cpp tiny_lexer-core-engine.cpp 
OBJS      = $(SOURCES:.cpp=.o)      messaging-framework.o
UTF8_OBJS = $(SOURCES:.cpp=-utf8.o) messaging-framework-utf8.o

# (*) COMPILER SETTINGS ________________________________________________________
#     (change COMPILER to whatever you use as compiler on the command line,
#      e.g. "make COMPILER=icpc" will use intel's c++ compiler)
COMPILER = g++ -ggdb -Wall -pedantic 
CC = $(COMPILER) -I./ -I$(QUEX_PATH) $(NDEBUG_F) \
	 -DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED

CC_UTF8 = $(CC) -D__QUEX_OPTION_MESSAGE_UTF8 \
		        -DQUEX_TYPE_CHARACTER=wchar_t \
		        -DQUEX_OPTION_ENABLE_ICONV 

# (*) RULES ____________________________________________________________________
all: $(FILES)

# -- char application
          
%-conversion-direct.exe: %-conversion-direct.cpp $(UTF8_OBJS) $(QUEX_CORE) 
	$(CC_UTF8) -o $@ $< $(UTF8_OBJS) 

%-conversion.exe: %-conversion.cpp $(UTF8_OBJS) $(QUEX_CORE) 
	$(CC_UTF8) -o $@ $< $(UTF8_OBJS) 
          
%.exe: %.cpp $(OBJS) $(QUEX_CORE) 
	$(CC) -o $@ $< $(OBJS) 
          
%-utf8.o: %.cpp $(QUEX_CORE)
	$(CC_UTF8) -c $< -o $@  
          
%.o: %.cpp $(QUEX_CORE)
	$(CC) -c $< -o $@  
          
$(SOURCES): simple.qx $(QUEX_CORE)
	# Don't need to set '--iconv'. The flag 'QUEX_OPTION_ENABLE_ICONV'
	# does all what is required.
	quex -i simple.qx --engine tiny_lexer --token-policy users_token

# (*) HELPERS __________________________________________________________________
clean:	
	touch simple.qx
	rm -f tiny_lexer*
	rm -f $(SOURCES)
	rm -f tiny_lexer-configuration
	rm -f $(FILES)
	rm -f *.exe
	rm -f *.o
	rm -f copy fill point
	rm -f *.bak
