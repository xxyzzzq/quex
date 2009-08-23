#! /usr/bin/env bash
bug=2841726
if [[ $1 == "--hwut-info" ]]; then
    echo "nobody: $bug 0.44.2 Unknown exception on unicode properties"
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
