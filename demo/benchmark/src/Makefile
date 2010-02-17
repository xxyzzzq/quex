# PURPOSE: Makefile Demo Application of Quex
#
# ABSOLUTELY NO WARRANTY
#_______________________________________________________________________________
COMPILER     = g++    # icpc # g++ 
COMPILER_V   = 4.3.1  # 10.1 # 4.3.1
BUFFER_SIZE  = 65536
OPTIMIZATION = -O3 # -O3 # -ggdb # # --coverage #-ggdb # -O1 #-pg # -O3# -pg -Os
GENERATOR    = Quex#  Quex, Flex
PROFILER     = # -pg # '-pg' for gprof profiling information
CPU_MHZ      = -DCPU_FREQ_MHZ=`source ./get_cpu_mhz.sh` 

# (*) SETUP ____________________________________________________________________
SETUP= \
      -D'EMAIL="fschaef@users.sourceforge.net"' \
      -D'CPU_NAME="IntelCoreDuo"' \
      -D'CPU_CODE="T2400"' \
	  $(CPU_MHZ) \
	  -D'CC_OPTIMIZATION_FLAGS="$(OPTIMIZATION)"' \
      -D'CHARACTER_SIZE=((unsigned)(1))' \
	  -D'OS_NAME="linux-2"' \
	  -D'CC_NAME="$(COMPILER)"' \
	  -D'CC_VERSION="$(COMPILER_V)"' \
      -D'QUEX_SETTING_BUFFER_SIZE=$(BUFFER_SIZE)' \
	  -D'NOTE=""' 

.PHONY: clean cpu_mhz

# The following might be overwritten by the caller of make:
EXTRA_COMPILER_FLAG=# -lefence#

ifndef QUEX_PATH
    $(error The environment variable QUEX_PATH is not defined!)
endif
include $(QUEX_PATH)/quex/code_base/core.mkd

SOURCE_FILES     = lexer.cpp report.cpp main.cpp 

OBJECT_FILES    = $(SOURCE_FILES:.cpp=.o)  # object file w/o line and column counting
OBJECT_FILES_LC = $(OBJECT_FILES:.o=-lc.o) # object file w line and column counting

# (*) COMPILER SETTINGS ________________________________________________________
#     (change COMPILER to whatever you use as compiler on the command line,
#     e.g. "make COMPILER=icpc" will use intel's c++ compiler)
PROFILE_ACTIVATE = -fprofile-arcs -fprofile-values
PROFILE_USE      = -fbranch-probabilities
CC_CORE = $(COMPILER) $(EXTRA_COMPILER_FLAG) $(OPTIMIZATION) -Wno-deprecated -Wall \
		 -I./ -I$(QUEX_PATH)  \
		 $(SETUP) \
		 -D__QUEX_CORE_OPTION_SUPPORT_BEGIN_OF_LINE_PRE_CONDITION_DISABLED \
		 -DNDEBUG \
		 -DQUEX_OPTION_ASSERTS_DISABLED	\
		 -DQUEX_OPTION_AUTOMATIC_ANALYSIS_CONTINUATION_ON_MODE_CHANGE_DISABLED \
		 -DQUEX_BENCHMARK_SERIOUS \
		 # -D__QUEX_OPTION_DEBUG_STATE_TRANSITION_REPORTS \
		 # $(PROFILER)
		 #-DQUEX_SETTING_BUFFER_SIZE=64 \
		 # -D__QUEX_OPTION_UNIT_TEST \
		 # -D__QUEX_OPTION_UNIT_TEST_QUEX_BUFFER_LOADS \

CC = $(CC_CORE) \
	 -DQUEX_OPTION_LINE_NUMBER_COUNTING_DISABLED \
	 -DQUEX_OPTION_COLUMN_NUMBER_COUNTING_DISABLED 

CC_LC = $(CC_CORE) \
        -DQUEX_OPTION_LINE_NUMBER_COUNTING   \
        -DQUEX_OPTION_COLUMN_NUMBER_COUNTING 

LD = $(COMPILER) $(OPTIMIZATION) $(PROFILER)

# (*) RULES ____________________________________________________________________
#    lexer    --> application w/o line or column counting
#    lexer-lc --> application w/ line and column counting
all: lexer-quex lexer-quex-lc lexer-flex lexer-re2c

lexer-quex: quex_scan.o $(OBJECT_FILES) 
	$(CC)    -DANALYZER_GENERATOR_QUEX $< $(OBJECT_FILES) -o $@ 

lexer-quex-lc: quex_scan-lc.o $(OBJECT_FILES_LC) 
	$(CC_LC) -DANALYZER_GENERATOR_QUEX $< $(OBJECT_FILES_LC) -o $@ 

lexer-flex: flex_scan.c
	$(CC)    -DANALYZER_GENERATOR_FLEX $(OBJECT_FILES) $< -lfl -o $@ 

lexer-re2c: re2c_scan.c 
	$(CC)    -DANALYZER_GENERATOR_RE2C $(OBJECT_FILES) $< -o $@

# -- application
%.o: %.cpp 
	$(CC) -c $< -o $@

%.o: %.c 
	$(CC) -c $< -o $@

%-lc.o: %.cpp quex_scan 
	$(CC_LC) -c $< -o $@

%.asm: %.cpp 
	$(CC) -S $< -o $@

%.E: %.cpp 
	$(CC) -E $< -o $@


quex_scan.cpp: quex/c.qx $(QUEX_CORE)
	quex -i $< \
		 --engine quex_scan                   \
		 --no-string-accumulator              \
		 --token-offset 3                     \
		 --token-prefix TKN_                  \
	     --token-policy           users_token \
         --foreign-token-id-file  token-ids.h 

flex_scan.c: flex/c.lex
	flex $< -o $@

re2c_scan.c:  re2c/c-re2c.in
	re2c -F -si $< | sed -e 's/\#line[^\n]*//g' > $@
	
# (*) HELPERS __________________________________________________________________
clean:	
	rm -f lexer lexer-lc lexer-flex
	rm -f lexer-token lexer-lc-token lexer-flex-token
	rm -f c_lexer-token
	touch quex/c.qx
	rm -f lexer
	rm -f token_ids
	rm -f *.o
	rm -f *.bak
	rm -f *.asm
	rm -f *.gcno 
	rm -f *.gcda
	rm -f *.gcov
	rm -f lex.yy.c
	rm -f *.E
	rm -f re2c_scan.*
	rm -f flex_scan.*
	rm -f quex_scan.*

cpu_mhz:
	@echo $(CPU_MHZ)

