FILES = test-utf8

test-utf8: test.cpp
		g++ -I$(QUEX_PATH) -I.  \
		$<                      \
		-DTEST_UTF8             \
		-o $@ 

clean:
	rm -f *.o
	rm -f $(FILES)

