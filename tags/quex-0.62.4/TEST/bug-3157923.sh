#! /usr/bin/env bash
bug=3157923
if [[ $1 == "--hwut-info" ]]; then
    echo "fschaef: $bug Memory Leak by Components"
    exit
fi

tmp=`pwd`
cd $bug/ 
make >& tmp.txt
cat tmp.txt | awk '(/[Ww][Aa][Rr][Nn][Ii][Nn][Gg]/ || /[Ee][Rr][Rr][Oo][Rr]/) && ! /ASSERTS/ '
rm tmp.txt

valgrind --leak-check=full ./lexer >& tmp.txt
python ../show-valgrind.py

rm tmp.txt

# cleansening
make clean >& /dev/null
cd $tmp
