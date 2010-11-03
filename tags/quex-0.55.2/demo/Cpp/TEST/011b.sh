#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "demo/011b: Engine Encoding UTF16"
    echo "CHOICES:  LE, BE;"
    echo "SAME;"
    exit
fi
cd $QUEX_PATH/demo/Cpp/011
make clean >& /dev/null
make utf16-lexer-other >& tmp.txt
cat tmp.txt | awk '(/[Ww][Aa][Rr][Nn][Ii][Nn][Gg]/ || /[Ee][Rr][Rr][Oo][Rr]/) && ! /ASSERTS/ '
rm tmp.txt
valgrind --leak-check=full ./utf16-lexer-other $1 >& tmp.txt
python ../TEST/show-valgrind.py
rm -f tmp.txt
