#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "demo/010: Direct Buffer Access (Syntactically Chunked)"
    echo "CHOICES:  copy-ez, fill-ez;"
    echo "SAME;"
    exit
fi
cd $QUEX_PATH/demo/010
# if [[ $1 == "copy-ez" ]]; then
#   touch simple.qx
# fi
make  $1.exe >& tmp.txt
cat tmp.txt | awk ' ! /g\+\+/' | awk '/[Ww][Aa][Rr][Nn][Ii][Nn][Gg]/ { print; } /[Ee][Rr][Rr][Oo][Rr]/ { print; }'
valgrind --leak-check=full ./$1.exe >& tmp.txt
python ../TEST/show-valgrind.py
rm -f tmp.txt
make clean >& /dev/null
