#! /usr/bin/env bash
bug=3110544
if [[ $1 == "--hwut-info" ]]; then
    echo "fschaef: $bug 0.55.2 quex output --intervals with [...]"
    exit
fi

tmp=`pwd`
cd $bug/ 
make story >& tmp.txt
cat tmp.txt | awk '(/[Ww][Aa][Rr][Nn][Ii][Nn][Gg]/ || /[Ee][Rr][Rr][Oo][Rr]/) && ! /ASSERTS/ '
rm tmp.txt

# cleansening
make clean >& /dev/null
cd $tmp
