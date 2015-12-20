
SOURCES := test.c \
	       EasyLexer.c

INCLUDES := -I. -I$(QUEX_PATH) -I$(HWUT_PATH)/support/C

CC := gcc $(INCLUDES) $(SOURCES) -Wall -Werror \
	  -DQUEX_SETTING_BUFFER_SIZE=5 

# Other useful options for debugging:
# -DQUEX_OPTION_ASSERTS_DISABLED
# -DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED 
# -DQUEX_OPTION_DEBUG_SHOW

all: lexer

hwut-info:
	@echo lexer

lexer: no-drop.qx test.c Makefile
	quex -i no-drop.qx --language C -o EasyLexer
	$(CC) -DPRINT_TOKEN -o $@

clean:
	rm -f EasyLexer*
	rm -f *.o
	rm -f lexer
	rm -f tmp.*
	rm -f *.dot
