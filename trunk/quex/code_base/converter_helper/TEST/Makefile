FILES = test-utf8

test-utf8: common.cpp test-utf8.cpp
		g++ -I$(QUEX_PATH) -I. -I$(HWUT_PATH) \
		$^                      \
		-DTEST_UTF8             \
		-ggdb                   \
		-o $@ 

%.E: %.cpp
		g++ -E -I$(QUEX_PATH) -I. -I$(HWUT_PATH) \
		$<                      \
		-DTEST_UTF8             \
		-o $@ 

hwut-info:
	@echo $(FILES)

clean:
	rm -f *.o
	rm -f $(FILES)

