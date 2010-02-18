# PURPOSE: Makefile Demo Application of Quex
#
# ABSOLUTELY NO WARRANTY
#_______________________________________________________________________________
.PHONY: clean 


include info.mk

# (*) SETUP ____________________________________________________________________
SETUP= \
      -DEMAIL='"$(AUTHOR_EMAIL)"' \
      -DCPU_NAME=$(CPU_NAME) \
      -DCPU_CODE="$(CPU_CODE)" \
	  -DCPU_FREQ_MHZ=$(CPU_MHZ) \
	  -DCC_OPTIMIZATION_FLAGS="$(COMPILER_OPT)" \
      -DCHARACTER_SIZE="((unsigned)(1))" \
	  -DOS_NAME='"$(OS_NAME)"' \
	  -DCC_NAME="$(COMPILER)" \
	  -D'CC_VERSION=$(COMPILER_V)' \
      -DQUEX_SETTING_BUFFER_SIZE="$(BUFFER_SIZE)" \
	  -DNOTE="$(NOTE)"

ifndef QUEX_PATH
    $(error The environment variable QUEX_PATH is not defined!)
endif
include $(QUEX_PATH)/quex/code_base/core.mkd

SOURCES    = lexer.cpp report.cpp main.cpp

OBJECTS    = $(addprefix out/, $(SOURCES:.cpp=.o))  
OBJECTS_LC = $(OBJECTS:.o=-lc.o)                   # object file w/ line column counting

# (*) COMPILER SETTINGS ________________________________________________________
#     (change COMPILER to whatever you use as compiler on the command line,
#     e.g. "make COMPILER=icpc" will use intel's c++ compiler)
# PROFILE_ENABLE = -fprofile-arcs -fprofile-values
# PROFILE_USE    = -fbranch-probabilities
INCLUDE = -I. -I$(QUEX_PATH)  
WARNING = -Wno-deprecated -Wall -Wimplicit 
DEFINES = \
		 -DNDEBUG \
		 -D__QUEX_CORE_OPTION_SUPPORT_BEGIN_OF_LINE_PRE_CONDITION_DISABLED \
		 -DQUEX_OPTION_ASSERTS_DISABLED	\
		 -DQUEX_OPTION_AUTOMATIC_ANALYSIS_CONTINUATION_ON_MODE_CHANGE_DISABLED \
		 -DQUEX_BENCHMARK_SERIOUS 
		 # -D__QUEX_OPTION_DEBUG_STATE_TRANSITION_REPORTS \
		 # -DQUEX_SETTING_BUFFER_SIZE=64 \
		 # -D__QUEX_OPTION_UNIT_TEST \
		 # -D__QUEX_OPTION_UNIT_TEST_QUEX_BUFFER_LOADS \

CC_CORE = $(COMPILER) $(COMPILER_OPT) \
		  $(WARNING) $(INCLUDE) $(DEFINES) \
		  $(SETUP) 

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
EXECUTABLES = lexer-quex lexer-quex-lc lexer-flex lexer-re2c

all: $(addprefix out/, $(EXECUTABLES))

out/lexer-quex: out/quex_scan.cpp $(OBJECTS) 
	$(CC)    -DANALYZER_GENERATOR_QUEX $< $(OBJECTS) -o $@ 

out/lexer-flex: out/flex_scan.c   $(OBJECTS) 
	$(CC)    -DANALYZER_GENERATOR_FLEX $< $(OBJECTS) -lfl -o $@ 

out/lexer-re2c: out/re2c_scan.c   $(OBJECTS) 
	$(CC)    -DANALYZER_GENERATOR_RE2C $< $(OBJECTS) -o $@

out/lexer-quex-lc: out/quex_scan.cpp $(OBJECTS_LC) 
	$(CC_LC) -DANALYZER_GENERATOR_QUEX $< $(OBJECTS_LC) -o $@ 

# Core ________________________________________________________________________

out/%.o: in/%.cpp 
	$(CC) -c $< -o $@

out/%.o: in/%.c 
	$(CC) -c $< -o $@

out/%-lc.o: in/%.cpp quex_scan 
	$(CC_LC) -c $< -o $@

out/%.asm: in/%.cpp 
	$(CC) -S $< -o $@

out/%.E: in/%.cpp 
	$(CC) -E $< -o $@

# Scanners ____________________________________________________________________

out/quex_scan.cpp: in/quex/c.qx $(QUEX_CORE)
	quex -i $< \
         --foreign-token-id-file  in/token-ids.h \
	     --output-directory       out            \
		 --engine quex_scan                      \
		 --no-string-accumulator                 \
		 --token-offset 3                        \
		 --token-prefix TKN_                     \
	     --token-policy users_token 

out/flex_scan.c:  in/flex/c.lex
	flex $< -o $@

out/re2c_scan.c:  in/re2c/c-re2c.in
	re2c -F -si $< | sed -e 's/\#line[^\n]*//g' > $@
	
# (*) HELPERS __________________________________________________________________
clean:	
	rm -f out/*

cpu_mhz:
	@echo $(CPU_MHZ)

os_name:
	@echo $(OS_NAME)
