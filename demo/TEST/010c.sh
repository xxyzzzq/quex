#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "demo/010: Direct Buffer Access & Character Set Conversion"
    echo "CHOICES:  copy-conversion, copy-conversion-direct, fill-conversion-direct;"
    echo "SAME;"
    exit
fi
cd $QUEX_PATH/demo/010
if [[ $1 == "copy-conversion" ]]; then
    touch simple.qx
fi
make  $1.exe >& tmp.txt
cat tmp.txt | awk ' ! /g++/ { print; }' | awk '/[Ww][Aa][Rr][Nn][Ii][Nn][Gg]/ || /[Ee][Rr][Rr][Oo][Rr]/ '
valgrind --leak-check=full ./$1.exe >& tmp.txt
python ../TEST/show-valgrind.py
rm -f tmp.txt
cd $QUEX_PATH/demo/TEST
make clean >& /dev/null
