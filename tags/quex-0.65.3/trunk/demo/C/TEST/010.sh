#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "demo/010: Direct Buffer Access (Syntactically Chunked)"
    echo "CHOICES:  point, re-point, copy, copy-ez, fill, fill-ez, copy-conversion, copy-conversion-direct, fill-conversion-direct;"
    exit
fi
cd $QUEX_PATH/demo/C/010

# if [[ $2 == "FIRST" ]]; then
make clean >& /dev/null
# fi

make  $1.exe ASSERTS_ENABLED_F=YES >& tmp.txt

cat tmp.txt | awk ' ! /gcc/' | awk '/[Ww][Aa][Rr][Nn][Ii][Nn][Gg]/ || /[Ee][Rr][Rr][Oo][Rr]/ { print; }' | awk ' !/out of range/ && ! /getline/'
rm tmp.txt

valgrind --leak-check=full ./$1.exe >& tmp.txt

python $QUEX_PATH/TEST/show-valgrind.py
rm -f tmp.txt

if [[ $3 == "LAST" ]]; then
    make clean >& /dev/null
fi

