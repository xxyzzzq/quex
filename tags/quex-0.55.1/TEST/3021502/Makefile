all:
	quex -i simple.qx --language C -o Simple --token-memory-management-by-user
	gcc point.c Simple.c -I. -I$(QUEX_PATH) -o a.out

clean:
	rm Simple*
	rm a.out
