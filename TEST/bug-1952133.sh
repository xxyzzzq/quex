#! /usr/bin/env bash
bug=1952133
if [[ $1 == "--hwut-info" ]]; then
    echo "fschaef: $bug 0.24.11 Crash in Buffer Handling with tiny buffer size"
    echo "CHOICES: 29, 30, 127, 128, 129, 2499, 2500, 2501, 2502;"
    exit
fi

echo "## Buffer Size = $1"
tmp=`pwd`
cd $bug/ 

if [[ $2 == "FIRST" ]]; then
    make clean
else
    make mostlyclean
fi
make BUFFER_SIZE=$1 >& tmp.txt
cat tmp.txt | awk '/[Ww][Aa][Rr][Nn][Ii][Nn][Gg]/ { print; } /[Ee][Rr][Rr][Oo][Rr]/ { print; }'
rm tmp.txt
valgrind --leak-check=full ./lexer error-example.txt >& tmp.txt
python ../show-valgrind.py
rm tmp.txt
if [[ $3 == "LAST" ]]; then
    make clean
else
    make mostlyclean
fi

cd $tmp
