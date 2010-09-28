#! /usr/bin/env bash
bug=3030640
if [[ $1 == "--hwut-info" ]]; then
    echo "ymarkovitch: $bug 0.50.1 Adding .hpp extension to generated headers"
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
