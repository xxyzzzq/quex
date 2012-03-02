#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "demo/010: Direct Buffer Access (Syntactically Chunked)"
    echo "CHOICES:  point, re-point, copy, copy-ez, fill, fill-ez, copy-conversion, copy-conversion-direct, fill-conversion-direct, stdinlexer;"
    exit
fi
cd $QUEX_PATH/demo/Cpp/010

# if [[ $2 == "FIRST" ]]; then
make clean >& /dev/null
# fi

make  $1.exe ASSERTS_ENABLED_F=YES >& tmp.txt

cat tmp.txt | awk ' ! /g\+\+/' | awk '/[Ww][Aa][Rr][Nn][Ii][Nn][Gg]/ || /[Ee][Rr][Rr][Oo][Rr]/ { print; }' | awk ' !/out of range/'
rm tmp.txt

if [[ $1 == "stdinlexer" ]]; then
    echo "Hello World" | valgrind --leak-check=full ./stdinlexer.exe >& tmp0.txt
    echo "212 W32orld" | valgrind --leak-check=full ./stdinlexer.exe >& tmp1.txt
    cat tmp0.txt tmp1.txt >> tmp.txt
else
    valgrind --leak-check=full ./$1.exe >& tmp.txt
fi

python ../TEST/show-valgrind.py
rm -f tmp.txt

if [[ $3 == "LAST" ]]; then
    make clean >& /dev/null
fi

