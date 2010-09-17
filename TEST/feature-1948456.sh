#! /usr/bin/env bash
bug=1948456
if [[ $1 == "--hwut-info" ]]; then
    echo "fschaef: $bug (feature) Inheritance Info"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i simple.qx -o Simple
awk ' /^[ \t]+\*\// { exit; } /^[ \t]+\*/ && ! /Indentation/ { print; } ' Simple.cpp

# cleansening
rm -f Simple Simple.cpp Simple-* *.o tmp.txt
cd $tmp
