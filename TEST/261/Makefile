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
COMPILER   = g++ -ggdb -pedantic -Wconversion -Wall -Werror -DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED -W

CC = $(COMPILER)        \
	 -DPRINT_LINE_COLUMN_NUMBER \
	 -I./ -I$(QUEX_PATH)  # -DQUEX_OPTION_DEBUG_SHOW
     # -DQUEX_OPTION_ASSERTS_DISABLED
     # -DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED 
   
case1:
	quex -i                 case1.qx  \
	     --engine           Simple  \
		 --token-id-offset  0x1000     --debug-exception --language C
	$(CC) -o $@ ../lexer.c Simple.c 
          
case2:
	quex -i                 case2.qx  \
	     --engine           Simple  \
		 --token-id-offset  0x1000     --debug-exception --language C
	$(CC) -o $@ ../lexer.c Simple.c 

# (*) HELPERS __________________________________________________________________
clean:	
	rm -f Simple*
	rm -f *.o
	rm -f *.bak
	rm -f *.E
	rm -f case1 case2
