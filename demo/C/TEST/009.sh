#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "demo/009: Strings of 'char' and 'wchar_t'"
    echo "CHOICES:  lexer, wlexer, stdinlexer;"
    echo "SAME;"
    exit
fi
cd $QUEX_PATH/demo/C/009

make $1 >& /dev/null

if [[ $1 == "stdinlexer" ]]; then
    echo -e "Hello World\nbye\n" | valgrind --leak-check=full ./stdinlexer &>  tmp.txt
    echo -e "212 W32orld\nbye\n" | valgrind --leak-check=full ./stdinlexer &>> tmp.txt
else
    echo "Normal FILE input"                     &>  tmp.txt 
    valgrind --leak-check=full ./$1 FILE         &>> tmp.txt
    echo "Normal stringstream input"             &>> tmp.txt
    valgrind --leak-check=full ./$1 stringstream &>> tmp.txt
fi
python $QUEX_PATH/TEST/show-valgrind.py 

make clean &> /dev/null
