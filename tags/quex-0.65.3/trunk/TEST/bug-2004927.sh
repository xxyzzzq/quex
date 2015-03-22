#! /usr/bin/env bash
bug=2004927
if [[ $1 == "--hwut-info" ]]; then
    echo "attardi: $bug UTF-8 RE Extra Comma Matched"
    echo "CHOICES:  iconv, icu, codec;"
    echo "SAME;"
    exit
fi

tmp=`pwd`
cd $bug/ 
make lex_$1 > tmp.txt
cat tmp.txt | awk '(/[Ww][Aa][Rr][Nn][Ii][Nn][Gg]/ || /[Ee][Rr][Rr][Oo][Rr]/) && ! /ASSERTS/ '
rm tmp.txt
./lex_$1 example.txt 
make clean >& /dev/null
cd $tmp
