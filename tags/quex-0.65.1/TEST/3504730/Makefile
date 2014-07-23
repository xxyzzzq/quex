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
CC = gcc                              \
	 -I./ -I$(QUEX_PATH)              \
	 -Wall -Werror -DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED -Wconversion -pedantic     \
	 $(CCFLAG_ASSERTS) 
     # -DQUEX_OPTION_ASSERTS_DISABLED
     # -DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED 
     # -DQUEX_OPTION_DEBUG_SHOW
   
LD = $(COMPILER) 

# (*) RULES ____________________________________________________________________
simple: $(QUEX_PATH)/TEST/lexer.c  
	quex -i                 simple.qx  \
	     --engine           Simple     \
		 --token-id-offset  0x1000     \
		 --language         C          \
		 --debug-exception
	$(CC) $^ Simple.c -o $@ -DPRINT_TOKEN

more: $(QUEX_PATH)/TEST/lexer.c 
	quex -i                 more.qx  \
	     --engine           Simple   \
		 --token-id-offset  0x1000   \
		 --language         C        \
		 --debug-exception
	$(CC) $^ Simple.c -o $@ -DPRINT_TOKEN

# (*) HELPERS __________________________________________________________________
clean:	
	rm -f Simple*
	rm -f More*
	rm -f *.o
	rm -f *.bak
	rm -f *.E
	rm -f simple more
