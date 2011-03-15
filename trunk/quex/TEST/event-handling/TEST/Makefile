.PHONY: clean
TEST_FILES = transition.exe \
			 transition-x.exe \
			 on_skip_range_open.exe \
			 on_skip_range_open-customized.exe 

ifndef QUEX_PATH
    $(error The environment variable QUEX_PATH is not defined!)
endif

include $(QUEX_PATH)/quex/code_base/core.mkd

# (*) SETUP ____________________________________________________________________
# (*) COMPILER SETTINGS ________________________________________________________
#     (change COMPILER to whatever you use as compiler on the command line,
#     e.g. "make COMPILER=icpc" will use intel's c++ compiler)
COMPILER = g++
LD = $(COMPILER) -Wno-deprecated -Wall \
	 -I./ -I$(QUEX_PATH) \
	 -DQUEX_OPTION_DEBUG_SHOW_MODES \
	 -DQUEX_OPTION_COLUMN_NUMBER_COUNTING_DISABLED \
	 -DQUEX_OPTION_LINE_NUMBER_COUNTING_DISABLED \
     -ggdb \
	 # -DQUEX_OPTION_DEBUG_SHOW

# (*) RULES ____________________________________________________________________
# -- application
all: $(TEST_FILES)

hwut-info:
	@echo $(TEST_FILES)

transit%.exe: transit%.qx lexer.cpp $(QUEX_CORE)
	$(QUEX_PATH)/quex-exe.py -i $< --engine EHLexer --token-prefix TK_ --token-policy single
	$(LD) ./lexer.cpp EHLexer.cpp -o $@ \
		-D__TEST_DESCRIPTION='"Mode Transitions: $<"' \
		-D__TEST_CHOICES='"1, 2, 3, error"'

on_skip_range_open.exe: on_skip_range_open.qx $(QUEX_CORE)
	$(QUEX_PATH)/quex-exe.py -i $< --engine EHLexer --token-policy single --token-prefix TK_
	$(LD) ./lexer.cpp EHLexer.cpp -o $@ \
		-D__TEST_DESCRIPTION='"Default 'on_skip_range_open' event."' \
		-D__TEST_CHOICES='"default"' \
          -DQUEX_SETTING_BUFFER_SIZE=4 \

on_skip_range_open-customized.exe: on_skip_range_open-customized.qx $(QUEX_CORE)
	$(QUEX_PATH)/quex-exe.py -i $< --engine EHLexer --token-policy single --token-prefix TK_
	$(LD) ./lexer.cpp EHLexer.cpp -o $@ \
		-D__TEST_DESCRIPTION='"Customized 'on_skip_range_open' event."' \
		-D__TEST_CHOICES='"customized"' \
          -DQUEX_SETTING_BUFFER_SIZE=4 \

# (*) HELPERS __________________________________________________________________
clean:	
	rm -f EHLexer*
	rm -f EasyLexer*
	rm -f lexer.o
	rm -f lexer
	rm -f token_ids
	rm -f *.bak
	rm -f $(TEST_FILES)
