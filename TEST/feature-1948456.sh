#! /usr/bin/env bash
bug=1948456
if [[ $1 == "--hwut-info" ]]; then
    echo "fschaef: $bug (feature) Inheritance Info"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i simple.qx -o Simple --comment-mode-patterns
awk 'BEGIN { allow_f = 0; } /MODE: FOUR/ { allow_f = 1; } /^[ \t]+\*/ { if( allow_f) print; } /END: MODE PATTERNS/ { exit; }' Simple.cpp

# cleansening
rm -f Simple Simple.cpp Simple-* *.o tmp.txt
cd $tmp
