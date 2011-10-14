#! /usr/bin/env bash
bug=3392478
if [[ $1 == "--hwut-info" ]]; then
    echo "denkfix: $bug UTF-8 Backward Input Position Detection Error"
    exit
fi

tmp=`pwd`
cd $bug/ 
make >& tmp.txt
cat tmp.txt | awk '(/[Ww][Aa][Rr][Nn][Ii][Nn][Gg]/ || /[Ee][Rr][Rr][Oo][Rr]/) && ! /ASSERTS/ '
./test
rm tmp.txt

# cleansening
make clean >& /dev/null
cd $tmp
