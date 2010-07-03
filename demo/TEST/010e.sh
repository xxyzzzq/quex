#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "demo/010: Pointing to User Memory"
    exit
fi
cd $QUEX_PATH/demo/010

make  point.exe >& tmp.txt
cat tmp.txt | awk ' ! /g++/ { print; }' | awk '/[Ww][Aa][Rr][Nn][Ii][Nn][Gg]/ || /[Ee][Rr][Rr][Oo][Rr]/ '
rm -f tmp.txt

valgrind --leak-check=full ./point.exe >& tmp.txt

python ../TEST/show-valgrind.py
rm -f tmp.txt 
make clean >& /dev/null

cd $QUEX_PATH/demo/TEST
