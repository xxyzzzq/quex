#! /usr/bin/env bash
bug=3526210
if [[ $1 == "--hwut-info" ]]; then
    echo "liancheng: $bug 0.62.4 Accumulator misbehaviour when no text is to be flushed"
    exit
fi

tmp=`pwd`
cd $bug/ 
make all >& tmp.txt
cat tmp.txt | awk '(/[Ww][Aa][Rr][Nn][Ii][Nn][Gg]/ || /[Ee][Rr][Rr][Oo][Rr]/) && ! /ASSERTS/ '
./string example.txt
rm tmp.txt Lexer* string

# cleansening
cd $tmp
