#! /usr/bin/env bash
bug=261
if [[ $1 == "--hwut-info" ]]; then
    echo "dlazesz: $bug Track Analysis--dangerous paths."
    echo "CHOICES: 1, 2;"
    exit
fi

tmp=`pwd`
cd $bug/ 
make case$1 >& tmp.txt
cat tmp.txt | awk '(/[Ww][Aa][Rr][Nn][Ii][Nn][Gg]/ || /[Ee][Rr][Rr][Oo][Rr]/) && ! /ASSERTS/ '
rm tmp.txt

./case$1 case$1.txt

# cleansening
make clean >& /dev/null
cd $tmp
