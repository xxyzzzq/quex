#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "demo/010: Direct Buffer Access & Character Set Conversion"
    echo "CHOICES:  copy-conversion, copy-conversion-direct, fill-conversion-direct;"
    echo "SAME;"
    exit
fi
cd $QUEX_PATH/demo/010
make clean >& /dev/null
make  $1.exe >& tmp.txt
cat tmp.txt | awk ' ! /g++/ { print; }' | awk '/[Ww][Aa][Rr][Nn][Ii][Nn][Gg]/ { print; } /[Ee][Rr][Rr][Oo][Rr]/ { print; }'
./$1.exe 
cd $QUEX_PATH/demo/TEST
