#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "demo/010: Direct Buffer Access (Syntactically Chunked)"
    echo "CHOICES:  copy, fill;"
    echo "SAME;"
    exit
fi
cd $QUEX_PATH/demo/010
make  $1-ez.exe >& tmp.txt
cat tmp.txt | awk '/[Ww][Aa][Rr][Nn][Ii][Nn][Gg]/ { print; } /[Ee][Rr][Rr][Oo][Rr]/ { print; }'
./$1-ez.exe 
make clean >& /dev/null
