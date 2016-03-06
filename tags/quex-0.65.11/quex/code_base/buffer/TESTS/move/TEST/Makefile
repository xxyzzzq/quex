
TEST_FILES = \
		   move_away_passed_content-fb0.exe \
		   move_away_passed_content-fb1.exe \
		   move_away_passed_content-fb2.exe \
		   move_away_passed_content-fb2-32.exe \
		   move_away_upfront_content-8.exe \
		   move_away_upfront_content-16.exe \
		   move_away_upfront_content-32.exe \

DEFS = \
	   \
	   -D__QUEX_OPTION_UNIT_TEST_QUEX_BUFFER_LOADS \
	   -DQUEX_OPTION_ASSERTS

CC_PURE := g++ \
		  -Wall -Werror -ggdb \
		  -I. -I$(QUEX_PATH) -I$(HWUT_PATH)/support/C \
		  $(DEFS) 

CC := g++ -DQUEX_TYPE_LEXATOM=uint8_t \
		  -Wall -Werror -ggdb \
		  -I. -I$(QUEX_PATH) -I$(HWUT_PATH)/support/C \
		  $(DEFS) 

all: $(TEST_FILES)

hwut-info:
	@echo $(TEST_FILES)

hwut-end: clean
	@echo Bye

%-gen.c: %.cpp
	hwut gen $< -o $(@:.c=)

move_away_passed_content-fb0.exe: move_away_passed_content.cpp \
	                          move_away_passed_content-gen.o \
							  hwut_cursor.o
	$(CC) $< -DQUEX_SETTING_BUFFER_MIN_FALLBACK_N=0 \
		  move_away_passed_content-gen.o hwut_cursor.o -o $@

move_away_passed_content-fb1.exe: move_away_passed_content.cpp \
	                          move_away_passed_content-gen.o \
							  hwut_cursor.o
	$(CC) $< -DQUEX_SETTING_BUFFER_MIN_FALLBACK_N=1 \
		  move_away_passed_content-gen.o hwut_cursor.o -o $@

move_away_passed_content-fb2.exe: move_away_passed_content.cpp \
	                          move_away_passed_content-gen.o \
							  hwut_cursor.o
	$(CC) $< -DQUEX_SETTING_BUFFER_MIN_FALLBACK_N=2 \
		  move_away_passed_content-gen.o hwut_cursor.o -o $@

move_away_passed_content-fb2-32.exe: move_away_passed_content.cpp \
	                                 move_away_passed_content-gen.o \
							         hwut_cursor.o
	$(CC_PURE) $< -DQUEX_SETTING_BUFFER_MIN_FALLBACK_N=2 \
		  -DQUEX_TYPE_LEXATOM=uint32_t \
		  move_away_passed_content-gen.o hwut_cursor.o -o $@

move_away_upfront_content-8.exe: move_away_upfront_content.cpp \
	                             move_away_upfront_content-gen.o \
							     hwut_cursor.o
	$(CC_PURE) $< -DQUEX_TYPE_LEXATOM=uint8_t \
          -DQUEX_SETTING_BUFFER_MIN_FALLBACK_N=0 \
		  move_away_upfront_content-gen.o hwut_cursor.o -o $@

move_away_upfront_content-16.exe: move_away_upfront_content.cpp \
	                              move_away_upfront_content-gen.o \
							      hwut_cursor.o
	$(CC_PURE) $< -DQUEX_TYPE_LEXATOM=uint16_t \
          -DQUEX_SETTING_BUFFER_MIN_FALLBACK_N=0 \
		  move_away_upfront_content-gen.o hwut_cursor.o -o $@

move_away_upfront_content-32.exe: move_away_upfront_content.cpp \
	                              move_away_upfront_content-gen.o \
							      hwut_cursor.o
	$(CC_PURE) $< -DQUEX_TYPE_LEXATOM=uint32_t \
          -DQUEX_SETTING_BUFFER_MIN_FALLBACK_N=0 \
		  move_away_upfront_content-gen.o hwut_cursor.o -o $@


%.o: %.c
	$(CC) -c $< -o $@

hwut_cursor.o: $(HWUT_PATH)/support/C/hwut_cursor.c 
	$(CC) -c $< -o $@

%.exe: %.cpp 
	g++ -DQUEX_TYPE_LEXATOM=uint32_t \
		-Wall -Werror \
		-ggdb -I. -I$(QUEX_PATH) -I$(HWUT_PATH)/support/C \
		$< -o $@

%.E: %.cpp 
	g++ -E -DQUEX_TYPE_LEXATOM=uint8_t -I$(HWUT_PATH)/support/C -I$(QUEX_PATH) $(DEFS) $< -o $@

%-32.exe: %.cpp 
	g++ -DQUEX_TYPE_LEXATOM=uint32_t \
		-Wall -Werror \
		-ggdb -I. -I$(QUEX_PATH) -I$(HWUT_PATH)/support/C \
		$(DEFS) $< -o $@

clean: 
	rm -rf $(TEST_FILES)
	rm -rf *.o
	rm -rf *-gen.[ch]
	rm -rf *.exe
