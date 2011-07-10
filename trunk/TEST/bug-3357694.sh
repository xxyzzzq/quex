#! /usr/bin/env bash
bug=3357694
if [[ $1 == "--hwut-info" ]]; then
    echo "denkfix: $bug Matches too long when using certain post condition"
    exit
fi

tmp=`pwd`
cd $bug/ 
make test >& tmp.txt
cat tmp.txt | awk '(/[Ww][Aa][Rr][Nn][Ii][Nn][Gg]/ || /[Ee][Rr][Rr][Oo][Rr]/) && ! /ASSERTS/ '
rm tmp.txt

./test

# cleansening
make clean >& /dev/null
cd $tmp
