#! /usr/bin/env bash
bug=2001602
if [[ $1 == "--hwut-info" ]]; then
    echo "attardi: $bug RE matching UTF8 l quote uno"
    echo "CHOICES: iconv, icu, codec;"
    echo "SAME;"
    exit
fi

tmp=`pwd`
cd $bug/ 
make lex_$1 > tmp.txt
cat tmp.txt | awk '(/[Ww][Aa][Rr][Nn][Ii][Nn][Gg]/ || /[Ee][Rr][Rr][Oo][Rr]/) && ! /ASSERTS/ && !/Wall/'
rm tmp.txt

./lex_$1 test.utf8
make clean >& /dev/null
cd $tmp
