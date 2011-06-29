#! /usr/bin/env bash
bug=2971198
if [[ $1 == "--hwut-info" ]]; then
    echo "kromaks: $bug 0.48.1 Parsing long REs"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i error.qx -o Simple >& tmp.txt

cat tmp.txt | awk '(/[Ww][Aa][Rr][Nn][Ii][Nn][Gg]/ || /[Ee][Rr][Rr][Oo][Rr]/) && ! /ASSERTS/ '
rm tmp.txt
ls Simple*

# cleansening
rm -f Simple*

cd $tmp
