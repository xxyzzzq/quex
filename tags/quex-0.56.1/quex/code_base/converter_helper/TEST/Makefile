FILES = characters \
		from-utf8  \
		from-utf16 \
		from-utf32  


CC = g++ -Wall -W -I$(QUEX_PATH) -I. -I$(HWUT_PATH) -ggdb 

all: $(FILES)

characters: characters.cpp
		$(CC) $^ -o $@ 

from-utf8: basics.cpp
		$(CC) $^ -o $@ -DSOURCE_NAME=utf8 -DSOURCE_TYPE=uint8_t 

from-utf16: basics.cpp
		$(CC) $^ -o $@ -DSOURCE_NAME=utf16 -DSOURCE_TYPE=uint16_t 

from-utf32: basics.cpp
		$(CC) $^ -o $@ -DSOURCE_NAME=utf32 -DSOURCE_TYPE=uint32_t 


%.E: %.cpp
		g++ -E -I$(QUEX_PATH) -I. -I$(HWUT_PATH) \
		$<                      \
		-DTEST_UTF8             \
		-DSOURCE_NAME=utf8      \
		-DSOURCE_TYPE=uint8_t   \
		-o $@ 

hwut-info:
	@echo $(FILES)

clean:
	rm -f *.o
	rm -f $(FILES)

