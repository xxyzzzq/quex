#! /usr/bin/env bash
bug=2002474
if [[ $1 == "--hwut-info" ]]; then
    echo "attardi: $bug Segmentation Fault while UTF-8 Decoding"
    echo "CHOICES:  iconv, icu, codec;"
    echo "SAME;"
    exit
fi

tmp=`pwd`
cd $bug/ 
make lex_$1 > tmp.txt
cat tmp.txt | awk '(/[Ww][Aa][Rr][Nn][Ii][Nn][Gg]/ || /[Ee][Rr][Rr][Oo][Rr]/) && ! /ASSERTS/ '
rm tmp.txt
make wiki.txt
./lex_$1 wiki.txt > tmp.txt
tail --lines=20 tmp.txt
rm tmp.txt

# cleansening
make clean >& /dev/null
cd $tmp
