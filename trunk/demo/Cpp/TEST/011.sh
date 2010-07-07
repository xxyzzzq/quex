#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "demo/011: Engine Encoding (Example ISO8859-7)"
    echo "CHOICES:  iso8859-7, utf8;"
    echo "SAME;"
    exit
fi
cd $QUEX_PATH/demo/Cpp/011
make clean >& /dev/null
make $1-lexer >& tmp.txt
cat tmp.txt | awk ' ! /g\+\+/ ' | awk '/[Ww][Aa][Rr][Nn][Ii][Nn][Gg]/ { print; } /[Ee][Rr][Rr][Oo][Rr]/ { print; }'
rm tmp.txt
valgrind --leak-check=full ./$1-lexer >& tmp.txt
python ../TEST/show-valgrind.py
rm -f tmp.txt
