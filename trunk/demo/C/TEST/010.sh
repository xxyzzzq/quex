#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "demo/010: Direct Buffer Access (Syntactically Chunked)"
    echo "CHOICES:  point, re-point, copy, copy-ez, fill, fill-ez, copy-conversion, copy-conversion-direct, fill-conversion-direct, stdinlexer;"
    exit
fi
cd ../010

# if [[ $2 == "FIRST" ]]; then
make clean >& /dev/null
# fi

make  $1.exe ASSERTS_ENABLED_F=YES >& tmp.txt

cat tmp.txt | awk ' ! /g\+\+/' | awk '/[Ww][Aa][Rr][Nn][Ii][Nn][Gg]/ || /[Ee][Rr][Rr][Oo][Rr]/ { print; }' | awk ' !/out of range/ && ! /getline/'
rm tmp.txt

if [[ $1 == "stdinlexer" ]]; then
    echo -e "Hello World\nbye\n" | valgrind --leak-check=full ./stdinlexer.exe >& tmp0.txt
    echo -e "212 W32orld\nbye\n" | valgrind --leak-check=full ./stdinlexer.exe >& tmp1.txt
    cat tmp0.txt tmp1.txt >> tmp.txt
else
    valgrind --leak-check=full ./$1.exe >& tmp.txt
fi

python $QUEX_PATH/TEST/show-valgrind.py 
rm -f tmp.txt

if [[ $3 == "LAST" ]]; then
    make clean >& /dev/null
fi

