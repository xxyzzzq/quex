#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "demo/009: Strings of 'char' and 'wchar_t'"
    echo "CHOICES:  lexer, wlexer;"
    echo "SAME;"
    exit
fi
cd $QUEX_PATH/demo/Cpp/009
make $1 >& /dev/null

echo "Normal FILE input"                     &>  tmp.txt 
valgrind --leak-check=full ./$1 FILE         &>> tmp.txt
echo "Normal stringstream input"             &>> tmp.txt
valgrind --leak-check=full ./$1 stringstream &>> tmp.txt

python $QUEX_PATH/TEST/show-valgrind.py 

make clean &> /dev/null
