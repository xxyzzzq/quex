#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "demo/011b: Engine Encoding UTF16"
    echo "CHOICES:  LE, BE;"
    echo "SAME;"
    exit
fi
cd $QUEX_PATH/demo/011
make clean >& /dev/null
make utf16-lexer >& tmp.txt
cat tmp.txt | awk ' ! /g\+\+/ ' | awk '/[Ww][Aa][Rr][Nn][Ii][Nn][Gg]/ { print; } /[Ee][Rr][Rr][Oo][Rr]/ { print; }'
rm tmp.txt
./utf16-lexer $1
