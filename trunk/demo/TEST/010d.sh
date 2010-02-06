#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "demo/010: Standard Input"
    exit
fi
cd $QUEX_PATH/demo/010
if [[ $1 == "copy-conversion" ]]; then
    touch simple.qx
fi
make  stdinlexer.exe >& tmp.txt
cat tmp.txt | awk ' ! /g++/ { print; }' | awk '/[Ww][Aa][Rr][Nn][Ii][Nn][Gg]/ || /[Ee][Rr][Rr][Oo][Rr]/ '
echo "Hello World" | valgrind --leak-check=full ./stdinlexer.exe >& tmp0.txt
echo "212 W32orld" | valgrind --leak-check=full ./stdinlexer.exe >& tmp1.txt
cat tmp0.txt tmp1.txt >> tmp.txt
python ../TEST/show-valgrind.py
rm -f tmp.txt tmp0.txt tmp1.txt
cd $QUEX_PATH/demo/TEST
make clean >& /dev/null
