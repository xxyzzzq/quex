#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "demo/009: Strings of 'char' and 'wchar_t'"
    echo "CHOICES:  lexer, wlexer, stdinlexer;"
    echo "SAME;"
    exit
fi
cd ../009

make $1 >& /dev/null

if [[ $1 == "stdinlexer" ]]; then
    echo -e "Hello World\nbye\n" | valgrind --leak-check=full ./stdinlexer >& tmp0.txt
    echo -e "212 W32orld\nbye\n" | valgrind --leak-check=full ./stdinlexer >& tmp1.txt
    echo "##"
    cat tmp0.txt tmp1.txt > tmp.txt
else
    echo "Normal FILE input"
    valgrind --leak-check=full ./$1 FILE         >& tmp0.txt
    echo "Normal stringstream input"
    valgrind --leak-check=full ./$1 stringstream >& tmp1.txt
    cat tmp0.txt tmp1.txt > tmp.txt
fi
python $QUEX_PATH/TEST/show-valgrind.py 

make clean >& /dev/null
