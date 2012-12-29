# PURPOSE: Makefile Demo Application of Quex
#
# ABSOLUTELY NO WARRANTY
#_______________________________________________________________________________
.PHONY: clean

ifndef QUEX_PATH
    $(error The environment variable QUEX_PATH is not defined!)
endif

include $(QUEX_PATH)/quex/code_base/core.mkd

# (*) COMPILER SETTINGS ________________________________________________________
#     (change COMPILER to whatever you use as compiler on the command line,
#      e.g. "make COMPILER=icpc" will use intel's c++ compiler)
COMPILER   = g++ -ggdb -pedantic -Wconversion -Wall -W

CC = $(COMPILER)        \
	 -I./ -I$(QUEX_PATH)  -DQUEX_OPTION_DEBUG_SHOW
     # -DQUEX_OPTION_ASSERTS_DISABLED
     # -DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED 
   
case1:
	quex -i                 case1.qx  \
	     --engine           EasyLexer  \
		 --token-id-offset  0x1000     --debug-exception
	$(CC) -o $@ example.cpp EasyLexer.cpp 
          
case2:
	quex -i                 case2.qx  \
	     --engine           EasyLexer  \
		 --token-id-offset  0x1000     --debug-exception
	$(CC) -o $@ example.cpp EasyLexer.cpp 

# (*) HELPERS __________________________________________________________________
clean:	
	rm -f EasyLexer*
	rm -f *.o
	rm -f *.bak
	rm -f *.E
	rm -f case1 case2
