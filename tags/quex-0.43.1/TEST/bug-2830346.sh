#! /usr/bin/env bash
bug=2830346
if [[ $1 == "--hwut-info" ]]; then
    echo "prombergerm: $bug 0.41.2: Multiple Lexers"
    exit
fi

tmp=`pwd`
cd $bug/ 

make story >& tmp.txt
cat tmp.txt | awk '(/[Ww][Aa][Rr][Nn][Ii][Nn][Gg]/ || /[Ee][Rr][Rr][Oo][Rr]/) && ! /ASSERTS/ '
rm tmp.txt

./story

# cleansening
make clean >& /dev/null
cd $tmp
