FILES = from-utf8

from-utf8: common.cpp basics.cpp
		g++ -I$(QUEX_PATH) -I. -I$(HWUT_PATH) \
		$^                      \
		-DTEST_UTF8             \
		-DSOURCE_NAME=utf8      \
		-DSOURCE_TYPE=uint8_t   \
		-ggdb                   \
		-o $@ 

characters: characters.cpp
		g++ -I$(QUEX_PATH) -I. -I$(HWUT_PATH) \
		$^                      \
		-ggdb                   \
		-liconv                 \
		-o $@ 

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

